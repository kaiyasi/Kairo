import re
import json
from typing import Optional, Dict, Any, List
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from .tenant import BookkeepingSettings

class GoogleSheetsManager:
    def __init__(self, credentials_path: str = None):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CREDENTIALS_PATH')
        self.service = None
        if self.credentials_path and os.path.exists(self.credentials_path):
            self._authenticate()

    def _authenticate(self):
        try:
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=SCOPES)
            self.service = build('sheets', 'v4', credentials=creds)
        except Exception as e:
            print(f"Google Sheets 認證失敗: {e}")
            self.service = None

    def extract_sheet_id(self, url: str) -> Optional[str]:
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None

    def get_sheet_values(self, sheet_id: str, range_name: str) -> Optional[List[List]]:
        if not self.service:
            return None
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        except HttpError as e:
            print(f"讀取 Google Sheets 失敗: {e}")
            return None

    def append_values(self, sheet_id: str, sheet_name: str, values: List[List]) -> bool:
        if not self.service:
            return False
        try:
            range_name = f"{sheet_name}!A1"
            body = {'values': values}
            self.service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            return True
        except HttpError as e:
            print(f"寫入 Google Sheets 失敗: {e}")
            return False

    def write_record_by_layout(self, sheet_id: str, settings: BookkeepingSettings, data: Dict[str, Any]) -> bool:
        if not self.service:
            return False
        try:
            all_values = self.get_sheet_values(sheet_id, 'Journal')
            target_row = settings.start_row
            if all_values:
                target_row = max(len(all_values) + 1, settings.start_row)

            requests = []
            for field, value in data.items():
                col_letter = getattr(settings, f"{field}_col")
                col_num = self.col_to_num(col_letter)
                requests.append({
                    'updateCells': {
                        'rows': [{
                            'values': [{
                                'userEnteredValue': {
                                    'stringValue': str(value) if not isinstance(value, (int, float)) else None,
                                    'numberValue': value if isinstance(value, (int, float)) else None
                                }
                            }]
                        }],
                        'start': {
                            'sheetId': self.get_sheet_id_by_name(sheet_id, 'Journal'),
                            'rowIndex': target_row - 1,
                            'columnIndex': col_num - 1
                        },
                        'fields': 'userEnteredValue'
                    }
                })

            if not requests:
                return True

            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
            return True
        except Exception as e:
            print(f"依版面設定寫入 Google Sheets 失敗: {e}")
            return False

    def get_sheet_id_by_name(self, spreadsheet_id: str, sheet_name: str) -> Optional[int]:
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            return 0 # Fallback to 0 if not found
        except Exception:
            return 0

    def col_to_num(self, col_str: str) -> int:
        num = 0
        for char in col_str:
            num = num * 26 + (ord(char.upper()) - ord('A')) + 1
        return num

    def create_journal_sheet(self, sheet_id: str) -> bool:
        if not self.service:
            return False
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            if 'Journal' not in sheet_names:
                requests = [{'addSheet': {'properties': {'title': 'Journal'}}}]
                self.service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={'requests': requests}).execute()
                headers = [['Date', 'Category', 'Amount', 'Memo', 'User']]
                self.append_values(sheet_id, 'Journal', headers)
            return True
        except HttpError as e:
            print(f"建立 Journal 工作表失敗: {e}")
            return False

    def get_balance_from_summary(self, sheet_id: str) -> Optional[float]:
        pass

    def calculate_balance_from_journal(self, sheet_id: str, amount_col: str) -> Optional[Dict[str, Any]]:
        try:
            values = self.get_sheet_values(sheet_id, f'Journal!{amount_col}:{amount_col}')
            if not values:
                return {'balance': 0, 'count': 0, 'source': 'Journal 計算 (0 筆記錄)'}

            total = 0
            count = 0
            # Skip header by trying to convert to float
            for row in values:
                if row:
                    try:
                        amount = float(str(row[0]).replace(',', ''))
                        total += amount
                        count += 1
                    except (ValueError, IndexError):
                        continue
            return {'balance': total, 'count': count, 'source': f'Journal 計算 ({count} 筆記錄)'}
        except Exception as e:
            print(f"計算 Journal 餘額失敗: {e}")
            return None

    def _is_number(self, value) -> bool:
        try:
            float(str(value).replace(',', ''))
            return True
        except (ValueError, TypeError):
            return False

    def export_journal_csv(self, sheet_id: str) -> Optional[str]:
        pass

def get_guild_google_sheets_url(guild_id: int) -> Optional[str]:
    import sqlite3
    with sqlite3.connect("data/tenant.db") as conn:
        cursor = conn.execute("SELECT excel_path FROM org_configs WHERE guild_id = ?", (guild_id,))
        row = cursor.fetchone()
        return row[0] if row and row[0] else None

def set_guild_google_sheets_url(guild_id: int, url: str) -> bool:
    import sqlite3
    try:
        with sqlite3.connect("data/tenant.db") as conn:
            conn.execute("INSERT OR REPLACE INTO org_configs (guild_id, excel_path) VALUES (?, ?)", (guild_id, url))
        return True
    except Exception as e:
        print(f"設置 Google Sheets URL 失敗: {e}")
        return False
