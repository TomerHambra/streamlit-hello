import streamlit as st
import asyncio
from streamlit_extras.add_vertical_space import add_vertical_space
import httpx, csv
from bs4 import BeautifulSoup, Tag
import re

class Maker:
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
        class_id: str,
        htmls: dict[str, str],
        url: str,
        schoolid: int,
        control: str
    ):
        tags = tags.copy()
        tags.update(
            {
                f"dnn$ctr{schoolid}$TimeTableView$ClassesList": class_id,
                f"dnn$ctr{schoolid}$TimeTableView$ControlId": control,
            }
        )

        response = await client.post(url, data=tags, headers={"encoding": "utf8"})
        htmls[class_id] = response.text


    def get_class_name_from_lesson(lesson_tag: Tag) -> str:
        return lesson_tag.find("b").next_sibling.text.strip()[1:-1]



    def get_all_class_names(html: str) -> set[str]:
        soup = BeautifulSoup(html, "lxml")
        return {
            self.get_class_name_from_lesson(tag)
            for tag in soup.find_all("div", {"class": "TTLesson"})
        }

    def extract_changes_table(cell: str, day: int) -> set[str]:
        classes = set()
        changes = cell.table
        if changes:
            changes = changes.find_all("tr")
            if changes:
                # classes = handle_fill_changes(changes, classes)
                classes = get_changes(changes)
        return classes

    # def get_changes(changes: set[str]):
    #     classes = {}
    #     print(changes)
        
    #     return classes
        


    def get_changes(changes: set[str]) -> set[str]:
        classes = set()
        for change in changes:
            swaps = change.find_all('td', {'class': 'TableFillChange'})
            if not swaps: continue
            swap = swaps[0].text
            ind = swap.find(':')
            if ind != -1:
                ind += 2
                classes.add(swap[ind:])
            else:
                nums = re.findall(r'\b\d+\b', swap)
                if not nums: continue
                clas = int(nums[-1])
                if clas > 100:
                    classes.add(str(clas))
        return classes

    def get_taken_classes_on_date(cell: str) -> set[str]:
        lessons = cell.find_all("div", {"class": "TTLesson"})
        return { self.get_class_name_from_lesson(lesson) for lesson in lessons }

    # THIS FUNCTIONS IS A BIT FASTER
    def get_available_classes_on_date(htmls: list[str], day: int, hour: int, bar) -> set[str]:
        available_classes = set().union(
            *(self.get_all_class_names(html) for html in htmls)
        ) # NOTE: this function is slow af, need to fix it
        for html in htmls:
            soup = BeautifulSoup(html, "lxml")
            table = soup.find("table", {"class": "TTTable"})
            row = table.find_all("tr", {'valign': 'top'})[hour]
            cell = row.find_all("td", {"class": "TTCell"})[day]
            available_classes -= get_taken_classes_on_date(cell)
            available_classes -= extract_changes_table(cell, day)
        return available_classes

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

    async def download_htmls() -> dict[str, str]:
        async with httpx.AsyncClient(headers={"encoding": "utf8"}) as client:
            tags, class_ids = await get_initial_form_data(client, self.url)
            client.cookies.clear()
            self.htmls = dict[str, str]()
            async with asyncio.TaskGroup() as tg:
                for class_id in class_ids:
                    tg.create_task(get_class_data(client, tags, class_id, self.htmls, self.url, self.schoolid, self.control))
            for clas in htmls.keys():
                with open(f'{schoolid}\\html-{self.schoolid}-{clas}.csv', 'w') as f:
                    f.write(htmls[clas])
            return htmls

    

if __name__ == '__main__':
    run()