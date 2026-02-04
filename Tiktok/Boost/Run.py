from multiprocessing import Process
from worker import *
from worker_seeding import *
from Tool import *

rows = get_bold_phone_rows_2(
    spreadsheet_id="14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8",
    sheet_name="seeding_2"
)


if __name__ == "__main__":
    processes = []
    for data in rows:
        p = Process(target=running_buff_view, args=(data,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()




