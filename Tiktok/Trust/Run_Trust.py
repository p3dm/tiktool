from multiprocessing import Process
from Trust import main_flow, get_bold_phone_rows

rows = get_bold_phone_rows(
    spreadsheet_id="14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8",
    sheet_name="seeding"
)

if __name__ == "__main__":
    print(rows)
    processes = []
    for data in rows:
        p = Process(target=main_flow, args=(data,))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()