# Copyright RoomFinder 2023 @
#
#     All rights remain in the hands of Tomer Hambra,
#     Ilay Nadler, and Roy Sigman. Any violation of this Copyright 
#     will cost in a lawsuit.
#  
#     https://roomfinder.streamlit.app


import streamlit as st
import asyncio
from streamlit_extras.add_vertical_space import add_vertical_space
import httpx, csv
from bs4 import BeautifulSoup, Tag
import re, os

class Maker:
    
    urls = {
        '':'',
        'Reali - Beit Biram':'https://beitbiram.iscool.co.il/default.aspx', 
        'Rabinky':'https://rabinky.iscool.co.il/default.aspx'
    }
    schoolids = {
        'https://beitbiram.iscool.co.il/default.aspx':7126,
        'https://rabinky.iscool.co.il/default.aspx':7121
    }
    control = {
        'https://beitbiram.iscool.co.il/default.aspx':'8',
        'https://rabinky.iscool.co.il/default.aspx':'8'
    }
    dicter = {
        '':0, 'Sunday': 15, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6
    }
    dicter2 = {
        '':0, '07:20 - 08:00': 15, '08:00 - 08:45': 1, '08:45 - 09:30': 2, '09:45 - 10:30': 3, '10:30 - 11:15': 4,
        '11:30 - 12:15': 5, '12:15 - 13:00': 6, '13:30 - 14:15': 7, '14:15 - 15:00': 8, '15:00 - 15:45': 9,
        '15:45 - 16:30': 10, '16:30 - 17:15': 11, '17:15 - 18:00': 12, '18:00 - 18:45': 13, '18:45 - 18:00': 14
    }
    
    def __init__(self, Url: str, schoolId: str, Control: str):
        self.url = Url
        self.schoolid = schoolId
        self.control = Control
    
    async def get_initial_form_data(self, 
        client: httpx.AsyncClient, url: str
    ) -> tuple[dict[str, str], list[str]]:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, "lxml")

        tags = {
            tag["id"]: tag.get("value")
            for tag in soup.find_all("input")
            if tag.get("value") is not None
        }
        class_ids = [option.get("value") for option in soup.find_all("option")]
        return tags, class_ids


    async def get_class_data(self, 
        client: httpx.AsyncClient,
        tags: dict[str, str],
        class_id: str
    ):
        tags = tags.copy()
        tags.update(
            {
                f"dnn$ctr{self.schoolid}$TimeTableView$ClassesList": class_id,
                f"dnn$ctr{self.schoolid}$TimeTableView$ControlId": self.control,
            }
        )

        response = await client.post(self.url, data=tags, headers={"encoding": "utf8"})
        
        open(f'htmls/{self.schoolid}/html-{class_id}.txt', "w").close()
        with open(f'htmls/{self.schoolid}/html-{class_id}.txt', "w") as f:
            f.write(response.text)


    def get_class_name_from_lesson(self, lesson_tag: Tag) -> str:
        return lesson_tag.find("b").next_sibling.text.strip()[1:-1]



    def get_all_class_names(self, html: str) -> set[str]:
        soup = BeautifulSoup(html, "lxml")
        return {
            self.get_class_name_from_lesson(tag)
            for tag in soup.find_all("div", {"class": "TTLesson"})
        }

    def extract_changes_table(self, cell: str, day: int) -> set[str]:
        classes = set()
        changes = cell.table
        if changes:
            changes = changes.find_all("tr")
            if changes:
                # classes = handle_fill_changes(changes, classes)
                classes = self.get_changes(changes)
        return classes

    # def get_changes(changes: set[str]):
    #     classes = {}
    #     print(changes)
        
    #     return classes
        


    def get_changes(self, changes: set[str]) -> set[str]:
        classes = set()
        for change in changes:
            swaps = change.find_all('td', {'class': 'TableFillChange'})
            if swaps:
                classes = classes.union(Maker.handle_fills(swaps))
                continue
            swaps = change.find_all('td', {'class': 'TableEventChange'})
            if swaps: 
                classes = classes.union(Maker.handle_events(swaps))
                continue
            swaps = change.find_all('td', {'class': 'TableExamChange'})
            if swaps: 
                l = Maker.handle_exams(swaps)
                classes = classes.union(l) 
        return classes

    def handle_exams(swaps) -> set[str]:
        retu = set()
        swap = swaps[0].text[::-1]
        num = ''
        found = False
        for c in swap:
            if c.isdigit():
                num += c
                found = True
            elif found: break
        if num == '': return retu
        clas = int(num[::-1])
        if clas > 100: retu.add(str(clas))
        return retu

    def handle_events(swaps) -> set[str]:
        retu = set()
        swap = swaps[0].text[::-1]
        num = ''
        found = False
        for c in swap:
            if c.isdigit():
                num += c
                found = True
            elif found: break
        if num == '': return retu
        clas = int(num[::-1])
        if clas > 100: retu.add(str(clas))
        return retu

    def handle_fills(swaps) -> set[str]:
        retu = set()
        swap = swaps[0].text
        ind = swap.find(':')
        if ind != -1:
            ind += 2
            retu.add(swap[ind:])
            return retu
        nums = re.findall(r'\b\d+\b', swap)
        if not nums: return retu
        clas = int(nums[-1])
        if clas > 100:
            l = str(clas)
            retu.add(l)
        return retu


    def get_taken_classes_on_date(self, cell: str) -> set[str]:
        lessons = cell.find_all("div", {"class": "TTLesson"})
        return { self.get_class_name_from_lesson(lesson) for lesson in lessons }

    # THIS FUNCTIONS IS A BIT FASTER
    def get_available_classes_on_date_in_class(self, day: int, hour: int, rooms: set[str], class_id: str) -> set[str]:
        
        with open(f'htmls/{self.schoolid}/html-{class_id}.txt', "r") as html:
            html = html.read()
            soup = BeautifulSoup(html, "lxml")
            table = soup.find("table", {"class": "TTTable"})
            row = table.find_all("tr", {'valign': 'top'})[hour]
            l = row.find_all("td", {"class": "TTCell"})
            if day >= len(l) or day < 0: return rooms 
            cell = l[day]
            rooms -= self.get_taken_classes_on_date(cell)
            rooms -= self.extract_changes_table(cell, day)
        
        return rooms

    #
    # FUNCTION IS SLOW BECAUSE OF DICTS AND FINDING FUNKY KLASSES
    #def get_available_classes_on_date(
    #    htmls: dict[str, str], day: int, hour: int
    #) -> set[str]:
    #    available_classes = set().union(
    #        *(get_all_class_names(html) for html in htmls.values())
    #    )
    #    for klass, html in htmls.items():
    #        taken_classes = get_taken_classes_on_date(html, day, hour)
    #        print(f"Class {klass} took rooms {taken_classes}")
    #        available_classes -= taken_classes
    #    return available_classes

    async def download_htmls(self, url: str, schoolid: str, control: str) -> list[str]:
        async with httpx.AsyncClient(headers={"encoding": "utf8"}) as client:
            tags, self.class_ids = await self.get_initial_form_data(client, url)
            client.cookies.clear()
            async with asyncio.TaskGroup() as tg:
                for class_id in self.class_ids:
                    tg.create_task(self.get_class_data(client, tags, class_id))
            # for clas in htmls.keys():
            #     with open(f'html{clas}.txt', 'w') as f:
            #         f.write(htmls[clas])

    def print_rooms(rooms: list[str]):
        # st.success('Program found {} rooms available: \n\n{}'.format(len(rooms), '\n'.join(f'- {room}' for room in rooms if not room == "")))
        good = []
        meh = []
        c = '\n'
        l = [good.append(s) if Maker.good_room(s) else meh.append(s) for s in rooms]
        st.success(f'Program found {len(good)} good rooms available: \n\n{c.join(f"- {room}" for room in good if not room == "")}')
        st.warning(f'Program found {len(meh)} rooms that are probably locked, but you can still try them: \n\n{c.join(f"- {room}" for room in meh if not room == "")}')

    def good_room(s: str) -> bool:
        return s.isnumeric() and int(s) < 600 and s[:2] != '50'

    def run(self) -> set[str]:
        total = set()
        for class_id in self.class_ids:
            with open(f'htmls/{self.schoolid}/html-{class_id}.txt', "r") as html:
                total = total.union(self.get_all_class_names(html.read()))
                
        for day in Maker.dicter.values():
            for hour in Maker.dicter2.values():
                if day and hour and self.url != '':
                    if hour == 15:
                        hour = 0
                    if day == 15:
                        day = 0
                    
                    rooms = total.copy()
                    for class_id in self.class_ids: 
                        rooms = self.get_available_classes_on_date_in_class(day, hour, rooms, class_id)
                    print(rooms)
                    
                    # ~ 2 secs for window -> 2 * 7 * 14 * 2 secs + 15 secs ~ 6.75 mins per calculation + 5 mins waiting ====> all fine :like:
                    open(f'results/{self.schoolid}/res-{day}-{hour}.txt', "w").close()
                    with open(f'results/{self.schoolid}/res-{day}-{hour}.txt', "w") as f:
                        f.write(str(rooms))
                    
                    
                    if hour == 0:
                        hour = 15
                    if day == 0:
                        day = 15
                
         
