import gspread, os, datetime

def update_google_sheet(date_str, value, username, balance):
    date_str = date_str.split()[0]
    gc = gspread.service_account(filename="applier/bot/utils/creds.json")
    
    spreadsheet = gc.open(os.environ.get("TABLE_NAME", "DM_accounting"))
    sheet = spreadsheet.sheet1

    sheet_id = sheet.id

    # Получение всех дат из первой строки, начиная с колонки B (вторая колонка)
    dates = []
    col = 2  # Начинаем с колонки B
    while True:
        date_cell = sheet.cell(1, col).value
        if date_cell:
            dates.append((date_cell, col))
            col += 3  # Переходим к следующей дате
        else:
            break  # Прерываем цикл, если ячейка пуста

    # Проверяем, существует ли дата
    date_cols = {date: col for date, col in dates}
    if date_str in date_cols:
        date_col = date_cols[date_str]
    else:
        # Добавляем новую дату в конец
        date_col = len(dates) * 3 + 2  # +2, потому что начинаем с колонки B
        sheet.update_cell(1, date_col, date_str)
        # Добавляем подзаголовки
        sheet.update_cell(2, date_col, 'Сумма чеков')
        sheet.update_cell(2, date_col + 1, 'Баланс')
        sheet.update_cell(2, date_col + 2, 'Кол-во чеков')
        date_cols[date_str] = date_col

        # Объединяем ячейки для даты и применяем форматирование
        merge_and_format_request = {
            "requests": [
                {
                    "mergeCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,  # Нулевая индексация (Row 1)
                            "endRowIndex": 1,    # Не включая строку 1 (только Row 1)
                            "startColumnIndex": date_col - 1,  # Нулевая индексация
                            "endColumnIndex": date_col + 2     # Объединяем 3 колонки
                        },
                        "mergeType": "MERGE_ALL"
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": date_col - 1,
                            "endColumnIndex": date_col + 2
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "horizontalAlignment": "CENTER",
                                "textFormat": {
                                    "bold": True
                                },
                                "backgroundColor": {
                                    "red": 0.8,
                                    "green": 0.95,
                                    "blue": 0.8,
                                    "alpha": 1
                                }
                            }
                        },
                        "fields": "userEnteredFormat(horizontalAlignment,textFormat,backgroundColor)"
                    }
                }
            ]
        }
        # Выполняем запрос на объединение ячеек и применение форматирования
        spreadsheet.batch_update(merge_and_format_request)

    # Получение всех имен пользователей из первого столбца, начиная с третьей строки
    usernames_col = sheet.col_values(1)[2:]  # Пропускаем первые две строки
    # Составляем словарь {username: row_number}
    user_rows = {}
    row = 3  # Начинаем с третьей строки
    for uname in usernames_col:
        if uname:
            user_rows[uname] = row
        row += 1

    # Проверяем, существует ли пользователь
    if username in user_rows:
        user_row = user_rows[username]
    else:
        # Добавляем нового пользователя в конец
        user_row = len(usernames_col) + 3  # +3, потому что начинаем с третьей строки
        sheet.update_cell(user_row, 1, username)
        user_rows[username] = user_row

    # Чтение существующих значений
    value_cell = sheet.cell(user_row, date_col).value
    balance_cell = sheet.cell(user_row, date_col + 1).value
    calls_cell = sheet.cell(user_row, date_col + 2).value

    # Инициализация существующих значений
    existing_value = float(value_cell.replace(",", "")) if value_cell else 0
    existing_balance = float(balance_cell.replace(",", "")) if balance_cell else 0
    existing_calls = float(calls_cell.replace(",", "")) if calls_cell else 0

    # Обновление значений
    new_value = existing_value + value
    new_balance = existing_balance + balance
    new_calls = existing_calls + 1

    # Запись обновленных данных
    sheet.update_cell(user_row, date_col, new_value)
    sheet.update_cell(user_row, date_col + 1, new_balance)
    sheet.update_cell(user_row, date_col + 2, new_calls)

    # Обновляем границы только для заполненных ячеек
    max_row_index = user_row  # Последняя строка с данными
    max_column_index = date_col + 2  # Последняя колонка с данными

    borders_request = {
        "requests": [
            {
                "updateBorders": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,  # Нулевая индексация (Row 1)
                        "endRowIndex": max_row_index,
                        "startColumnIndex": 0,  # Нулевая индексация (Column A)
                        "endColumnIndex": max_column_index
                    },
                    "top": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {}
                    },
                    "bottom": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {}
                    },
                    "left": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {}
                    },
                    "right": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {}
                    },
                    "innerHorizontal": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {}
                    },
                    "innerVertical": {
                        "style": "SOLID",
                        "width": 1,
                        "color": {}
                    }
                }
            }
        ]
    }

    # Выполняем запрос на обновление границ
    spreadsheet.batch_update(borders_request)
    return