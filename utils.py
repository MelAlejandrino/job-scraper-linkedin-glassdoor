from typing import List, Dict, Optional, Any, Union
import pandas as pd
from jobspy import scrape_jobs

class LinkedinJobs:
    def __init__(self, job_title: str, location: str) -> None:
        self.title = [job_title]
        self.location = [location]
        self.platform = ["linkedin"]

    def fetch_listing(self) -> pd.DataFrame:
        jobs = scrape_jobs(
            site_name=self.platform,
            search_term=self.title[0],
            location=self.location[0],
            results_wanted=1000,  # High limit to fetch all available
            get_extra_details=True,
            linkedin_fetch_description=True
        )
        if not jobs.empty:
            jobs["job_title_searched"] = self.title[0]
            jobs["country"] = self.location[0]
        return jobs

class GlassdoorJobs:
    def __init__(self, job_title: str, location: str) -> None:
        self.title = [job_title]
        self.location = [location]
        self.platform = ["glassdoor"]

    def fetch_listing(self) -> pd.DataFrame:
        jobs = scrape_jobs(
            site_name=self.platform,
            search_term=self.title[0],
            location=self.location[0],
            results_wanted=1000,  # High limit to fetch all available
            get_extra_details=True
        )
        if not jobs.empty:
            jobs["job_title_searched"] = self.title[0]
            jobs["country"] = self.location[0]
        return jobs