from worker import *
from worker_seeding import *
from Tool import *
from flask import Flask, request, jsonify
from multiprocessing import Process
from worker import running_post_video

rows = get_bold_phone_rows(
    spreadsheet_id="14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8",
    sheet_name="seeding"
)


if __name__ == "__main__":
    processes = []
    for data in rows:
        p = Process(target=running_post_video, args=(data,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()




