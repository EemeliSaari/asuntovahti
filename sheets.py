from contextlib import contextmanager

import click
import gspread
from gspread.models import Worksheet
from oauth2client.service_account import ServiceAccountCredentials
from tornado.ioloop import IOLoop

from data import HouseEntry
from tasks import fetch_houses


class SheetWrapper:
    """SheetWrapper

    Wraps and keeps the ids in the memory

    Parameters
    ----------
    sheet : gspread.models.Worksheet
        Google Spreadsheet model
    """
    def __init__(self, sheet: Worksheet):
        self.sheet = sheet
        self.ids = set()

        records = self.sheet.get_all_records()
        if not records:
            self.sheet.insert_row(HouseEntry.fields(), 1)
        else:
            for record in records:
                self.ids.add(record['id'])

    def insert(self, entry: HouseEntry):
        """Insert new entry
        
        Automatically append to the end of the sheet

        Parameters
        ----------
        entry : HouseEntry
            Data container about the house
        """
        if entry.id not in self.ids:
            self.ids.add(entry.id)
            row = list(entry.asdict().values())
            self.sheet.insert_row(row, index=len(self.ids) + 1)
            print('FOUND A NEW ONE!', entry)
        else:
            print('ALREADY EXISTS', entry.id)


@contextmanager
def sheet_context(sheet_name: str, path: str='client_secret.json') -> SheetWrapper:
    """Sheet Context

    Opens a SheetWrapper as context

    Parameters
    ----------
    sheet_name : str
        Google Sheet name
    path : str
        Path to the user's secrets
    """
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(path, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    try:
        yield SheetWrapper(sheet=sheet)
    finally:
        pass


@click.command()
@click.option('--config', type='str', default='config.yaml')
@click.option('--sheet', type='str')
def main(config, sheet):
    with sheet_context(sheet) as s:
        fetch_houses(config, redirect=s.insert)
        IOLoop.instance().start()


if __name__ == '__main__':
    main()
