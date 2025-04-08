import pandas as pd
from tqdm import tqdm
from utils import LinkedinJobs, GlassdoorJobs
import re

job_titles = [
    "Software Engineer",
    "Systems Software Developer",
    "Research and Development computing professional",
    "Applications Software Developer",
    "Computer Programmer",
    "Systems Analyst",
    "Data Analyst",
    "Quality Assurance Specialist",
    "Software Support Specialist"
]

# Multiple locations to expand dataset
locations = ["Philippines", "United States", "India", "Canada", "United Kingdom"]

def extract_qualifications(description, source=None, job_desc=None):
    """Extract qualifications from job description"""
    if job_desc is not None:
        description = job_desc
    
    if not isinstance(description, str) or not description.strip():
        return "Qualifications not specified"
    
    try:
        clean_desc = re.sub(r'<[^>]+>', '', description)
        clean_desc = clean_desc.encode('utf-8', errors='ignore').decode('utf-8', errors='replace')
        clean_desc = re.sub(r'[â€¢â€™]', '', clean_desc)
        clean_desc = re.sub(r'â€', '', clean_desc)
        clean_desc = re.sub(r'\*+', '', clean_desc)

        patterns = [
            r'(?:minimum qualifications|qualifications|requirements|must have|need.*?|what you bring|required skills|experience|education|degree|preferred technical|technical expertise)(?:.*?[:\s-]*|\n)(.*?)(?=\n\s*\n|\n\s*(?:soft skills|work schedule|about us|responsibilities|apply now|benefits|equal opportunity|$))',
            r'(?:soft skills|personal skills|attributes|team player|communication skills)(?:.*?[:\s-]*|\n)(.*?)(?=\n\s*\n|\n\s*(?:work schedule|about us|apply now|benefits|equal opportunity|$))',
        ]
        
        extracted_quals = []
        for pattern in patterns:
            match = re.search(pattern, clean_desc, re.I | re.DOTALL)
            if match:
                quals = match.group(1).strip()
                bullets = re.findall(r'(?:•|\-|\d+\.|\*|\n)\s*([^\n•\-*]{10,})', quals, re.DOTALL)
                if bullets:
                    extracted_quals.extend(b.strip() for b in bullets if len(b.strip()) > 10)
                else:
                    lines = [line.strip() for line in quals.split('\n') if len(line.strip()) > 10]
                    extracted_quals.extend(lines)
        
        keywords = ['experience', 'skills', 'education', 'degree', 'certification', 'required', 'knowledge', 'ability', 'proficiency', 'expertise', 'bachelor', 'team player', 'communication']
        for line in clean_desc.split('\n'):
            line = line.strip()
            if len(line) > 200 or any(kw in line.lower() for kw in ['we are proud', 'our culture', 'app store', 'equal opportunity']):
                continue
            if any(kw in line.lower() for kw in keywords) and len(line) > 20 and line not in extracted_quals:
                extracted_quals.append(line)
        
        if extracted_quals:
            extracted_quals = [re.sub(r'[\n\r]+', ' ', qual).strip() for qual in extracted_quals]
            return "; ".join(extracted_quals[:15])
        return "Qualifications not specified in detail"
    except Exception as e:
        print(f"Error extracting qualifications: {e}")
        return "Error extracting qualifications"

def is_entry_level(description):
    """Check if job is entry-level or requires no experience"""
    if not isinstance(description, str):
        return False
    
    description = description.lower()
    entry_keywords = [
        "entry level", "entry-level", "no experience", "fresh graduate", "junior", "trainee", 
        "beginner", "starter", "0-1 year", "0 to 1 year", "new grad", "graduate", "fresher"
    ]
    exclude_keywords = [
        "senior", "mid-level", "experienced", "5+ years", "3+ years", "2+ years", 
        "expert", "lead", "manager", "supervisor"
    ]
    
    has_entry = any(keyword in description for keyword in entry_keywords)
    has_exclude = any(keyword in description for keyword in exclude_keywords)
    
    return has_entry and not has_exclude

def scrape_all_jobs():
    all_jobs = pd.DataFrame()
    
    for location in locations:
        print(f"\nScraping LinkedIn for {location}...")
        for title in tqdm(job_titles, desc=f"LinkedIn Jobs ({location})"):
            try:
                linkedin = LinkedinJobs(title, location)
                jobs = linkedin.fetch_listing()
                if not jobs.empty:
                    jobs = jobs[jobs['description'].apply(is_entry_level)]
                    if not jobs.empty:
                        jobs['qualifications'] = jobs['description'].apply(extract_qualifications)
                        jobs['source'] = 'LinkedIn'
                        jobs['location'] = location  # Add location to track country
                        all_jobs = pd.concat([all_jobs, jobs[['title', 'qualifications', 'source', 'location']]], ignore_index=True)
            except Exception as e:
                print(f"Error scraping LinkedIn {title} in {location}: {e}")
        
        print(f"\nScraping Glassdoor for {location}...")
        for title in tqdm(job_titles, desc=f"Glassdoor Jobs ({location})"):
            try:
                glassdoor = GlassdoorJobs(title, location)
                jobs = glassdoor.fetch_listing()
                if not jobs.empty:
                    jobs = jobs[jobs['description'].apply(is_entry_level)]
                    if not jobs.empty:
                        jobs['qualifications'] = jobs['description'].apply(extract_qualifications)
                        jobs['source'] = 'Glassdoor'
                        jobs['location'] = location  # Add location to track country
                        all_jobs = pd.concat([all_jobs, jobs[['title', 'qualifications', 'source', 'location']]], ignore_index=True)
            except Exception as e:
                print(f"Error scraping Glassdoor {title} in {location}: {e}")
    
    # Rename columns for final output
    all_jobs = all_jobs.rename(columns={'title': 'Title', 'qualifications': 'Qualifications', 'source': 'Source', 'location': 'Location'})
    return all_jobs

if __name__ == "__main__":
    print("Starting job scrape for entry-level/no-experience jobs across LinkedIn and Glassdoor...")
    print(f"Searching for: {', '.join(job_titles)}")
    print(f"Locations: {', '.join(locations)}\n")
    
    all_jobs = scrape_all_jobs()
    
    if not all_jobs.empty:
        # Optional: Deduplicate by title and company (if available) to avoid overlap
        all_jobs = all_jobs.drop_duplicates(subset=['Title', 'Source', 'Location'])
        output_file = "combined_entry_level_jobs_global.csv"
        all_jobs.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nSaved {len(all_jobs)} entry-level/no-experience jobs to {output_file}")
        
        print("\nSample job from each source:")
        for source in ['LinkedIn', 'Glassdoor']:
            sample_jobs = all_jobs[all_jobs['Source'] == source]
            if not sample_jobs.empty:
                sample = sample_jobs.iloc[0]
                print(f"\nSource: {source}")
                print(f"Title: {sample['Title']}")
                print(f"Location: {sample['Location']}")
                print(f"Qualifications: {sample['Qualifications'][:100]}...")
    else:
        print("\nNo entry-level/no-experience jobs found. Possible reasons:")
        print("- Job postings may not explicitly mention entry-level terms")
        print("- Check network connection or site availability")
        print("- Adjust entry_keywords in is_entry_level() if needed")