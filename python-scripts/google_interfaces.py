from __future__ import print_function
# google imports
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaIoBaseDownload, MediaFileUpload, MediaIoBaseUpload
# python imports
from os import getcwd, listdir
from io import BytesIO
import pickle
import os.path


# scopes for authentication
# came from google api docs
SHEET_SCOPE = 'https://www.googleapis.com/auth/<location>/'
DRIVE_SCOPE = 'https://www.googleapis.com/auth/<drive>'

# used for authenticating all scopes
SCOPES = [SHEET_SCOPE, DRIVE_SCOPE]

# only for testing, feel free to change these
TEST_ID = 'ID_KEY'
TEST_RANGE = 'SHEET_NAME'

# This class is inherited by DriveInterface and SheetsInterface
# THERE IS NO REASON TO CREATE AN INSTANCE OF THIS CLASS


class GoogleAPI():
    def __init__(self, scopes=SCOPES):
        self.scopes = scopes
        self.creds = self.get_creds()

    def get_creds(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.scopes)
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds


'''
SheetsInterface is a class for reading and manipulating Google Sheets
Each instance of SheetsInterface is dedicated to a single spreadsheet
to initialize:
    si = SheetsInterface(spread_id=your_spread_id)
'''


class SheetsInterface(GoogleAPI):
    '''
    initialize a SheetsInterface object
    args:
        scopes: (list of strings) optional
        spread_id: (string)
    returns:
        None
    '''

    def __init__(self, scopes=[SHEET_SCOPE], spread_id=TEST_ID):
        super(SheetsInterface, self).__init__(scopes=scopes)
        self.spreadsheet_id = spread_id
        self.service = build('sheets', 'v4', credentials=self.creds)

    '''
    read data from a google sheet
    args:
        range_name: (string)
    returns:
        values: (list of lists where each list is a row from the sheet)
    '''

    def get_sheet(self, range_name=TEST_RANGE):
        sheet_result = self.service \
            .spreadsheets() \
            .values() \
            .get(spreadsheetId=self.spreadsheet_id, range=range_name) \
            .execute()
        values = sheet_result.get('values')
        return values

    '''
    create a new spreadsheet in Google Drive
    args:
        title: (string)
    returns:
        response: not sure here, either a Google API or http response object
    '''

    def create_new_spreadsheet(self, title):
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        spreadsheet = self.service.spreadsheets().create(body=spreadsheet,
                                                         fields='spreadsheetId').execute()
        return spreadsheet

    '''
    add a new sheet to the spreadsheet
    args:
        title: (string) the name for the sheet
    returns:
        response: not sure here, either a Google API or http response object
    '''

    def add_sheet_to_spread(self, title):
        request = {
            'addSheet': {
                'properties': {
                    'title': title
                }
            }
        }
        body = {
            'requests': [request]
        }
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=body).execute()
        return response

    '''
    add a list of rows to a spreadsheet starting at the first empty cell in column 1
    args:
        sheet_name: (string) the name of the sheet to be appended to
        values: a list of rows (lists) to append to the sheet
    returns:
        a tuple with two elements
        first element: (bool) True if success, False if failure
        second element: not sure here, either a Google API or http response object
    '''

    def append_values_to_sheet(self, sheet_name, values=[]):
        body = {
            'values': [values]  # extra list seems wrong but is necessary
        }
        range_name = sheet_name + '!A1'
        value_input_option = 'USER_ENTERED'
        try:
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body).execute()
        except HttpError as e:
            return False, e
        return True, result

    '''
    get a list of the sheets in a spreadsheet
    args:
        None
    returns:
        sheets: (list of strings) the names of all sheets associated with a spreadsheet
    '''

    def get_sheets(self):
        response = self.service. \
            spreadsheets(). \
            get(spreadsheetId=self.spreadsheet_id). \
            execute()
        sheets = []
        for sheet in response['sheets']:
            sheets.append(sheet['properties']['title'])
        return sheets

    '''
    just like add_sheet_to_spread but writes headers to the first row
    args:
        sheet_name: (string) the name of the sheet to create
        col_names: (list of strings) the headers to write in the first row
    returns:
        success: (bool) True if successful, False if not
    '''

    def add_sheet_to_spread_with_col_names(self, sheet_name, col_names=[]):
        self.add_sheet_to_spread(sheet_name)
        if col_names:
            success, result = self.append_values_to_sheet(sheet_name,
                                                          values=col_names)
        return success


'''
DriveInterface is a class for downloading and uploading files to Google Drive
to initialize:
    di = DriveInterface()
'''


class DriveInterface(GoogleAPI):
    '''
    initialize a DriveInterface object
    args:
        scopes: (list of strings) optional
    returns:
        None
    '''

    def __init__(self):
        super(DriveInterface, self).__init__(scopes=[DRIVE_SCOPE])
        self.service = build('drive', 'v3', credentials=self.creds)

    '''
    create a new folder in Google Drive
    args:
        name: (string) the name of the folder to create
        parent_id: (string) the file id of the folder to place the new folder in
    returns:
        None
    '''

    def new_folder(self, name, parent_id=None):
        file_metadata = {'name': name,
                         'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        file = self.service.files().create(body=file_metadata,
                                           fields='id').execute()
        print('Folder ID: %s' % file.get('id'))

    '''
    upload a file to google drive
    args:
        fpath: (string) path to the file to upload
        folder_id: (string) the file id of the folder to put the file in
    returns:
        file id of the uploaded file
    '''

    def upload_file(self, fpath, folder_id=None):
        fname = fpath.split('/')[-1]
        file_metadata = {'name': fname,
                         'parents': [folder_id]}
        media = MediaFileUpload(fpath,
                                mimetype='image/jpeg',
                                resumable=True)
        file = self.service.files().create(body=file_metadata,
                                           media_body=media,
                                           fields='id').execute()
        print('File ID: %s' % file.get('id'))
        return 'https://drive.google.com/open?id=' + file.get('id')

    '''
    upload bytes of an image to Google Drive
    args:
        fbytes: (byte string) bytes representation of an image
        fname: (string) the name for the file created in Google Drive
        mtype: (string) the mimetype of the file being uploaded
        folder_id: (string) the file id of the folder to put the file in
    returns:
        url for linking to the uploaded file
    '''

    def upload_bytes(self, fbytes, fname, mtype='jpeg', folder_id=None):
        bio = BytesIO(fbytes)
        file_metadata = {'name': fname,
                         'parents': [folder_id]}
        media = MediaIoBaseUpload(bio,
                                  mimetype='image/' + mtype,
                                  resumable=True)
        file = self.service.files().create(body=file_metadata,
                                           media_body=media,
                                           fields='id').execute()
        print('File ID: %s' % file.get('id'))
        return 'https://drive.google.com/open?id=' + file.get('id')


if __name__ == '__main__':
    di = DriveInterface()
    fdir = '/home/plenty-user/Plenty/picam_array/pickles'
    fname = os.listdir(fdir)[0]
    fpath = os.path.join(fdir, fname)
    meta, imgb = pickle.load(open(fpath, 'rb'))
    di.upload_bytes(imgb, 'test.jpg',
                    folder_id='FOLDER_ID')
