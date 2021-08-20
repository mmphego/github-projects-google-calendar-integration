import argparse
import sys

from pathlib import Path

from dotenv import dotenv_values
from github import Github
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo", help="Github repo")
    parser.add_argument("-e", "--env", default=".env", help=".env file")
    parser.add_argument("-p", "--project", help="project name")
    parser.add_argument(
        "-g", "--google-dir", help="Directory containing Google Calendar credentials"
    )
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    return parser.parse_args()


def read_dotenv(env_file: str) -> dict:
    """Read configuration from file."""
    try:
        assert Path(env_file).exists()
        config = dotenv_values(env_file)
    except AssertionError:
        raise FileNotFoundError(
            f"Missing {env_file} file. See: https://pypi.org/project/python-dotenv/"
        )
    return config


def get_credentials_path(google_creds_dir):
    """Get credentials path."""
    try:
        assert Path(google_creds_dir).exists()
        creds_path = Path(google_creds_dir) / "credentials.json"
        token_path = Path(google_creds_dir) / "token.json"
    except AssertionError:
        raise FileNotFoundError(
            f"Missing {google_creds_dir} directory."
            " See: https://developers.google.com/calendar/quickstart/python"
        )
    return (token_path, creds_path)


class GoogleCalendar:
    def __init__(self, token_path: str, credentials_path: str):
        # The file token_pass `stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.`
        self.setup_service(token_path, credentials_path)
        self.calendar = None

    def setup_service(self, token_path: str, credentials_path: str):
        """Setup the Google Calendar service."""
        # If modifying these scopes, delete the file token_path.
        scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
        creds = Credentials.from_authorized_user_file(token_path, scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        self.calendar = build("calendar", "v3", credentials=creds)

    def create_event(self, task: dict):
        """Create a new event to the calender"""
        pass

    def update_event(self, task: dict):
        """Update a new event to the calender"""
        pass

    def clear_event(self):
        """Clear the event from the calender"""
        pass


class TaskCompleted:
    def __init__(self, gh: object, task: dict):
        self.gh = gh
        self.task = task

    def mark_task_complete(self):
        """Mark task that is completed by ticking the checkbox."""
        pass

    def move_task(self, column):
        """Move completed task to a specific"""
        pass


class Project:
    def __init__(self, repo_name: str, token: str):
        self._gh = Github(token)
        self._repo = self._gh.get_repo(repo_name)

    @staticmethod
    def get_high_priority_task(
        project_column, target_column: str = "In Progress (Priority)"
    ):
        """Get the high priority task from a specific column in the specified project."""
        column = [c for c in project_column if c.name == target_column][0]
        cards = column.get_cards()
        contents = [card.get_content() for card in cards]
        task = {}
        for content in contents:
            content_body = content.body.splitlines()
            task = {
                "title": content.title,
                "body": [c.replace("[ ] ", "") for c in content_body if "[ ]" in c][0],
            }
            break
        return task

    def get_project_columns(self, project_name: str):
        """Get all columns from a specific project."""
        if not project_name:
            return
        project = [p for p in self._repo.get_projects() if p.name == project_name][0]
        columns = [c for c in project.get_columns()]
        return columns


if __name__ == "__main__":
    args = parser()
    config = read_dotenv(args.env)

    creds_path = get_credentials_path(args.google_dir)
    google_calender = GoogleCalendar(*creds_path)

    project = Project(repo_name=args.repo, token=config["token"])
    project_columns = project.get_project_columns(args.project)
    priority_task = project.get_high_priority_task(project_columns)
