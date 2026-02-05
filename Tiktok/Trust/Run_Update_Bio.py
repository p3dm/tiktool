from multiprocessing import Process
from Trust import *
from Trust.Trust import get_bold_phone_rows, update_bio

rows = get_bold_phone_rows(
    spreadsheet_id="14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8",
    sheet_name="seeding"
)

if __name__ == "__main__":
    proccesses = []
    for data in rows:
       p = Process(target=update_bio, args=(data,))
       proccesses.append(p)
       p.start()
    for p in proccesses:
        p.join()
       

