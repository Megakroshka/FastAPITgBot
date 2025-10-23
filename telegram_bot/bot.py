import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- Константы ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = "http://fastapi_service:8000/products/"

# Определяем состояния для диалогов
# Диалог добавления
ADD_NAME, ADD_DESCRIPTION, ADD_PRICE = range(3)
# Диалог обновления
UPDATE_SELECT, UPDATE_NAME, UPDATE_DESCRIPTION, UPDATE_PRICE = range(3, 7)

# --- Вспомогательные функции ---

def get_product_details(product_id: int) -> dict | None:
    """Получает детали одного товара по ID."""
    try:
        response = requests.get(f"{API_URL}{product_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# --- Функции основных команд ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение со списком команд."""
    await update.message.reply_text(
        'Привет! Я бот для управления товарами.\n\n'
        'Доступные команды:\n'
        '/list - Показать все товары\n'
        '/add - Добавить новый товар\n'
        '/get <ID> - Показать информацию о товаре\n'
        '/update <ID> - Обновить товар\n'
        '/delete <ID> - Удалить товар\n'
        '/cancel - Отменить текущую операцию'
    )

async def get_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получает и отображает список всех товаров."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        products = response.json()
        if not products:
            message = "Товаров пока нет. Добавьте первый с помощью /add."
        else:
            message = "🛒 Список товаров:\n\n"
            for product in products:
                message += f"🆔 ID: {product['id']}\n"
                message += f"🏷️ Название: {product['name']}\n"
                message += f"💰 Цена: {product['price']}\n"
                message += "--------------------\n"
        await update.message.reply_text(message)
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f'Не удалось получить список товаров. Ошибка: {e}')

async def get_single_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получает и отображает один товар по ID."""
    try:
        product_id = int(context.args[0])
        product = get_product_details(product_id)
        if product:
            message = (
                f"📦 Детали товара ID {product['id']}:\n"
                f"🏷️ Название: {product['name']}\n"
                f"📝 Описание: {product['description']}\n"
                f"💰 Цена: {product['price']}"
            )
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(f"Товар с ID {product_id} не найден.")
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите ID товара. Пример: /get 1")

async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Удаляет товар по ID."""
    try:
        product_id = int(context.args[0])
        response = requests.delete(f"{API_URL}{product_id}")
        response.raise_for_status()
        await update.message.reply_text(f"Товар с ID {product_id} успешно удален.")
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите ID товара. Пример: /delete 1")
    except requests.exceptions.RequestException:
        await update.message.reply_text(f"Не удалось удалить товар с ID {product_id}. Возможно, он уже удален.")

# --- Диалог ДОБАВЛЕНИЯ товара ---

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Введите название нового товара.')
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text('Отлично! Теперь введите описание.')
    return ADD_DESCRIPTION

async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['description'] = update.message.text
    await update.message.reply_text('Описание сохранено. Теперь введите цену (число).')
    return ADD_PRICE

async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.replace(',', '.'))
        product_data = {
            "name": context.user_data['name'],
            "description": context.user_data['description'],
            "price": price
        }
        response = requests.post(API_URL, json=product_data)
        response.raise_for_status()
        await update.message.reply_text('✅ Товар успешно добавлен!')
    except (ValueError, KeyError):
        await update.message.reply_text('Что-то пошло не так. Попробуйте добавить товар заново. /add')
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f'Ошибка API: {e}')
    finally:
        context.user_data.clear()
    return ConversationHandler.END

# --- Диалог ОБНОВЛЕНИЯ товара ---

async def update_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог обновления."""
    try:
        product_id = int(context.args[0])
        product = get_product_details(product_id)
        if not product:
            await update.message.reply_text(f"Товар с ID {product_id} не найден.")
            return ConversationHandler.END
        
        context.user_data['product'] = product
        await update.message.reply_text(
            f"Обновляем товар: {product['name']}.\n"
            "Введите новое название или отправьте /skip, чтобы оставить старое."
        )
        return UPDATE_NAME
    except (IndexError, ValueError):
        await update.message.reply_text("Пожалуйста, укажите ID товара. Пример: /update 1")
        return ConversationHandler.END

async def update_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обновляет название или пропускает."""
    if update.message.text != '/skip':
        context.user_data['product']['name'] = update.message.text
    await update.message.reply_text("Введите новое описание или /skip, чтобы оставить старое.")
    return UPDATE_DESCRIPTION

async def update_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обновляет описание или пропускает."""
    if update.message.text != '/skip':
        context.user_data['product']['description'] = update.message.text
    await update.message.reply_text("Введите новую цену или /skip, чтобы оставить старую.")
    return UPDATE_PRICE

async def update_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обновляет цену и отправляет запрос в API."""
    product = context.user_data['product']
    try:
        if update.message.text != '/skip':
            product['price'] = float(update.message.text.replace(',', '.'))

        # Убираем ID из данных, которые отправляем в API
        product_id = product.pop('id')
        
        response = requests.put(f"{API_URL}{product_id}", json=product)
        response.raise_for_status()
        await update.message.reply_text('✅ Товар успешно обновлен!')

    except ValueError:
        await update.message.reply_text('Цена должна быть числом. Попробуйте еще раз.')
        return UPDATE_PRICE # Остаемся в том же состоянии
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f'Ошибка API: {e}')
    finally:
        context.user_data.clear()
    return ConversationHandler.END

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для команды /skip."""
    # Эта функция нужна, чтобы /skip не воспринимался как обычный текст
    # Логика пропуска реализована в самих функциях диалога
    # Мы просто перенаправляем на следующий шаг
    current_state = context.user_data.get('current_state')
    if current_state == UPDATE_NAME:
        return await update_name(update, context)
    if current_state == UPDATE_DESCRIPTION:
        return await update_description(update, context)
    if current_state == UPDATE_PRICE:
        return await update_price(update, context)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет любой диалог."""
    await update.message.reply_text('Действие отменено.')
    context.user_data.clear()
    return ConversationHandler.END

# --- Основная функция ---

def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Диалог для добавления
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Диалог для обновления
    update_conv = ConversationHandler(
        entry_points=[CommandHandler("update", update_start)],
        states={
            UPDATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_name)],
            UPDATE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_description)],
            UPDATE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        # Добавляем обработку /skip на каждом шаге
        map_to_parent={
            UPDATE_NAME: UPDATE_NAME,
            UPDATE_DESCRIPTION: UPDATE_DESCRIPTION,
            UPDATE_PRICE: UPDATE_PRICE,
        }
    )
    # Добавляем обработчик для /skip внутри диалога обновления
    update_conv.states[UPDATE_NAME].append(CommandHandler('skip', update_name))
    update_conv.states[UPDATE_DESCRIPTION].append(CommandHandler('skip', update_description))
    update_conv.states[UPDATE_PRICE].append(CommandHandler('skip', update_price))


    # Добавляем все обработчики в приложение
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", get_products))
    application.add_handler(CommandHandler("get", get_single_product))
    application.add_handler(CommandHandler("delete", delete_product))
    application.add_handler(add_conv)
    application.add_handler(update_conv)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()