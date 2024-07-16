import requests
from pydantic import BaseModel, Field
from typing import Tuple, List, Optional
import os


# Function to call Moodle API
def moodle_api_call(function_name, params):
    # Configuration
    MOODLE_URL = os.getenv("MOODLE_URL")
    API_TOKEN = os.getenv("MOODLE_API_TOKEN")
    REST_ENDPOINT = f"{MOODLE_URL}/webservice/rest/server.php"
    params["wstoken"] = API_TOKEN
    params["moodlewsrestformat"] = "json"
    params["wsfunction"] = function_name
    response = requests.get(REST_ENDPOINT, params=params)
    response.raise_for_status()
    return response.json()


def get_content_text(fileurl):
    API_TOKEN = os.getenv("MOODLE_API_TOKEN")
    params = {}
    params["wstoken"] = API_TOKEN
    response = requests.get(fileurl, params=params)
    response.raise_for_status()
    return response.json()


class MoodleModuleContent:
    def __init__(
        self,
        type: str,
        course_id: int = None,
        filename: Optional[str] = "",
        fileurl: Optional[str] = "",
        text: Optional[str] = "",
    ):
        self.type = type
        self.filename = filename
        self.fileurl = fileurl
        self.text = text

    def __str__(self):
        string = f"Filename: {self.filename}"
        if self.text:
            string += f", Content: {self.text}"
        return string

    def asdict(self):
        return {
            "filename": self.filename,
            "doc_type": "content",
            "course_id": self.course_id,
        }


class MoodleModule:
    def __init__(
        self,
        name: str,
        modname: str,
        url: str,
        course_id: int = None,
        description: Optional[str] = "",
        contents: List[MoodleModuleContent] = [],
    ):
        self.name = name
        self.description = description
        self.modname = modname
        self.url = url
        self.contents = contents

    def __str__(self):
        string = f"""
        Course Module {self.name}
        Type: {self.modname}
        URL: {self.url}
        Description: {self.description}
        """
        if len(self.contents) == 0:
            return string
        string += "\nContents:"
        for content in self.contents:
            string += "\n - " + str(content)
        return string

    def asdict(self):
        return {
            "name": self.name,
            "description": self.description,
            "doc_type": "module",
            "course_id": self.course_id,
        }


class MoodleCourseSection:
    def __init__(
        self,
        name: str,
        course_id: int = None,
        description: Optional[str] = "",
        modules: List[MoodleModule] = [],
    ):
        self.name = name
        self.description = description
        self.modules = modules

    def __str__(self):
        string = f"""
        Course Section {self.name}
        Description: {self.description}
        """
        if len(self.modules) == 0:
            return string
        string += "\nModules:"
        for module in self.modules:
            string += (
                "\n - Module Name " + module.name + ", Module Type " + module.modname
            )
        return string

    def asdict(self):
        return {
            "name": self.name,
            "description": self.description,
            "doc_type": "section",
            "course_id": self.course_id,
        }


class MoodleCourse:
    def __init__(
        self,
        id: int,
        name: str,
        summary: Optional[str] = "",
        sections: List[MoodleCourseSection] = [],
    ):
        self.id = id
        self.name = name
        self.summary = summary
        self.url = f"{os.getenv('MOODLE_URL')}/course/view.php?id={id}"
        self.sections = sections

    def __str__(self):
        string = f"""
        Course {self.name}
        URL: {self.url}
        Summary: {self.summary}
        """
        if len(self.sections) == 0:
            return string
        string += "\nSections:"
        for section in self.sections:
            string += "\n - " + section.name
        return string

    def asdict(self):
        return {
            "course_id": str(self.id),
            "name": self.name,
            "summary": self.summary,
            "url": self.url,
            "doc_type": "course",
        }


class MoodleSiteInfo:
    def __init__(
        self,
        name: str,
        url: str,
        summary: Optional[str] = "",
        courses: List[MoodleCourse] = [],
    ):
        self.name = name
        self.summary = summary
        self.url = url
        self.courses = courses

    def __str__(self):
        string = f"""
        Site Name: {self.name}
        URL: {self.url}
        Summary: {self.summary}
        """
        if len(self.courses) == 0:
            return string
        string += "\n" + str(len(self.courses)) + " courses available"

        if len(self.courses) > 10:
            string += "\nShowing first 10 courses"
            for i in range(min(10, len(self.courses))):
                course = self.courses[i]
                string += "\n - " + course.name
        else:
            for course in self.courses:
                string += "\n - " + course.name

        return string

    def asdict(self):
        return {
            "name": self.name,
            "summary": self.summary,
            "url": self.url,
            "doc_type": "site",
        }


# Get list of courses
def get_courses() -> MoodleSiteInfo:
    function_name = "core_course_get_courses"
    params = {}
    data = moodle_api_call(function_name, params)

    # First course is the site info
    if len(data) == 0:
        return None, []

    site_info = MoodleSiteInfo(
        name=data[0].get("fullname"),
        url=os.getenv("MOODLE_URL"),
        summary=data[0].get("summary"),
    )

    if len(data) < 2:
        return site_info, []

    courses = [
        MoodleCourse(
            id=course.get("id"),
            name=course.get("fullname"),
            summary=course.get("summary"),
        )
        for course in data[1:]
    ]

    site_info.courses = courses

    return site_info


# Get course sections
def get_course_sections(course_id) -> List[MoodleCourseSection]:
    function_name = "core_course_get_contents"
    params = {"courseid": course_id}
    data = moodle_api_call(function_name, params)
    sections = []
    for section in data:
        modules = []
        for module in section.get("modules"):
            contents = []
            if "contents" in module:
                for content in module.get("contents"):
                    if (
                        content.get("type") == "file"
                        and content.get("filename")
                        and content.get("filename").endswith(".html")
                    ):
                        contenttext = get_content_text(content.get("fileurl"))
                        contents.append(
                            MoodleModuleContent(
                                type="file",
                                filename=content.get("filename"),
                                fileurl=content.get("fileurl"),
                                text=contenttext,
                            )
                        )
                    else:
                        contents.append(
                            MoodleModuleContent(
                                type="file", filename=content.get("filename")
                            )
                        )
            modules.append(
                MoodleModule(
                    name=module.get("name"),
                    modname=module.get("modname"),
                    url=module.get("url"),
                    contents=contents,
                )
            )
        sections.append(
            MoodleCourseSection(
                name=section.get("name"),
                description=section.get("summary"),
                modules=modules,
            )
        )

    return sections


# Main function to scrape data
def scrape_moodle_data() -> MoodleSiteInfo:
    MOODLE_URL = (os.getenv("MOODLE_URL"),)
    site = get_courses()

    for course in site.courses:
        sections = get_course_sections(course.id)
        course.sections = sections

    return site
