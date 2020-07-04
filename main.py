import requests
from bs4 import BeautifulSoup
import csv
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.keys import Keys
import datetime
from random import randint


def sleepPlease():
    sleep(0.1)
    sleep(randint(0, 2))
    return None


def getSearchURLs(searchTerms, filters):
    res = []
    driver = webdriver.Chrome()
    # driver.get('https://www.glassdoor.ca/Job/ontario-jobs-SRCH_IL.0,7_IS4080.htm')
    driver.get('https://www.glassdoor.ca/Job/canada-engineer-jobs-SRCH_IL.0,6_IN3.htm')
    sleepPlease()

    for searchTerm in searchTerms:
        inputElement = driver.find_element_by_id("sc.keyword")
        inputElement.clear()
        sleep(0.1)
        inputElement.send_keys(searchTerm)
        inputElement.send_keys(Keys.ENTER)
        sleep(0.1)
        res.append(driver.current_url + filters)
        sleep(0.1)

    return res


def downloadCSV(result, file):
    keys = result[0].keys()
    with open('D:/Python Projects/Job Finder/jobCSVs/' + file, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(result)


def extractJobs(URL):
    try:
        # Navigate to the URL and pull all the jobs on it
        print(URL)
        jobListPage = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'})
        sleepPlease()
        soupJobListPage = BeautifulSoup(jobListPage.text, "html.parser")

        allJobMetaData = soupJobListPage.find_all(name="div", attrs={"class": "jobContainer"})
        allRatingMetaData = soupJobListPage.find_all(name="span", attrs={"class": "compactStars"})

        # Get the max number of pages we can search through
        PageHTML = soupJobListPage.find(name="div", attrs={"class": "cell middle hideMob padVertSm"}).get_text()
        splitPages = PageHTML.split()
        currentPage = int(splitPages[1])
        nextPage = currentPage + 1
        totalPages = int(splitPages[3])

        # For every job on the page, do this loop
        for j, div in enumerate(allJobMetaData, start=0):
            while True:
                try:
                    company = div.find_all(name="a", attrs={"class": "jobTitle"})[0].get_text()
                    ratingNo = allRatingMetaData[j].get_text()
                    jobLink = "https://www.glassdoor.ca" + div.find_all(name="a", attrs={"class": "jobTitle"})[1]["href"]
                    # Get job  details and a link to the job application page
                    jobMetaData = {
                        "companyName": company[1:],
                        "jobTitle": div.find_all(name="a", attrs={"class": "jobTitle"})[1].get_text(),
                        "location": div.find(name="span", attrs={"class": "loc"}).get_text(),
                        "rating": ratingNo.replace(" ", ""),
                        "applicationLink": jobLink
                    }

                    # Enter this loop if I don't already have this job stored, and it meets my rating threshold.
                    if (float(jobMetaData["rating"]) >= ratingFilter) and (float(jobMetaData["rating"]) <= upperRatingFilter) and ("paid" not in jobMetaData["companyName"]) and all(excluded not in jobMetaData["jobTitle"] for excluded in excludeList):
                        # If I already have a job stored from the same company, store the new one immediately since the company already passed my criteria.
                        if any(storedJob["companyName"] == jobMetaData["companyName"] for storedJob in jobDict):
                            if any(((storedJob["companyName"] == jobMetaData["companyName"]) and (storedJob["jobTitle"] == jobMetaData["jobTitle"])) for storedJob in jobDict):
                                break
                            else:
                                jobDict.append(jobMetaData)

                        # If the company hasn't been stored before, check how many reviews it has. Don't wanna get catfished by fake reviews.
                        else:
                            while True:
                                try:
                                    # Go to the job posting page to find the company's profile id
                                    jobPage = requests.get(jobLink, headers={'user-agent': 'Mozilla/5.0'})
                                    sleepPlease()
                                    soupJobPage = BeautifulSoup(jobPage.text, "html.parser")
                                    scriptTag = str(soupJobPage.find_all('script')[0])

                                    start = scriptTag.find("'id'", scriptTag.find("employer"))
                                    end = scriptTag.find(",", start)
                                    companyId = [int(i) for i in scriptTag[start: end:].replace('"', "").split() if
                                                 i.isdigit()]

                                    # Now that I have the company's id, I can visit the company's profile page on Glassdoor
                                    profileLink = "https://www.glassdoor.ca/Reviews/" + jobMetaData["companyName"].replace(" ", "-") + "-Reviews-E" + str(companyId[0]) + ".htm"
                                    companyProfile = requests.get(profileLink, headers={'user-agent': 'Mozilla/5.0'})
                                    sleepPlease()
                                    soupCompanyProfile = BeautifulSoup(companyProfile.text, "html.parser")

                                    # From the profile page, I can see how many reviews they have
                                    reviewsNumber = soupCompanyProfile.find_all(name="span", attrs={"class": "num h2"})[1].get_text()[1:]
                                    if "k" in reviewsNumber:
                                        reviewsNumber = float(reviewsNumber.replace("k", "")) * 1000

                                    # I'll only store the job if the company has over 35 reviews
                                    if float(reviewsNumber) > reviewLimit:
                                        jobDict.append(jobMetaData)

                                    # break and go to next job on the list
                                    break

                                except Exception as ex3:
                                    print("Error 3: ", ex3)
                                    continue
                    break
                except Exception as ex1:
                    print("Error 1: ", ex1)
                    continue

        # These statements control moving to the next page
        if (currentPage < totalPages) and (currentPage < NoOfPagesToSearch):
            if "_IP" not in URL:
                insertPosition = URL.find(".htm")
                newURL = URL[:insertPosition] + "_IP" + str(nextPage) + URL[insertPosition:]
                extractJobs(newURL)
            elif "_IP" in URL and currentPage < 10:
                insertPosition = URL.find("_IP") + 3
                newURL = URL[:insertPosition] + str(nextPage) + URL[1 + insertPosition:]
                extractJobs(newURL)
            elif "_IP" in URL and currentPage >= 10:
                insertPosition = URL.find("_IP") + 3
                newURL = URL[:insertPosition] + str(nextPage) + URL[2 + insertPosition:]
                extractJobs(newURL)
        return
    except Exception as ex2:
        print("Error 2: ", ex2)
        return

# Place search terms in list below
inputList = [
    "CEO",
]

# filterTerms = "?fromAge=30&minRating=3.0"  # How old the job posting is, and the company rating. Limited to what glassdoor allows.
filterTerms = "?minRating=4.0"  # Set to 3.0 if looking for companies below 4.0 rating.
ratingFilter = 4.0   # Lower limit for company rating
upperRatingFilter = 4.7  # Upper limit for company rating
NoOfPagesToSearch = 3  # Number of pages to search in the results
reviewLimit = 20  # Minimum number of reviews the company should have on Glassdoor.com to be considered.

# Example variables to find all internships in Ontario (location is set in the getSearchURLs function directly)
'''inputList = ["intern"]
filterTerms = ""
ratingFilter = 1
upperRatingFilter = 5
NoOfPagesToSearch = 30
reviewLimit = 0'''

excludeList = [] # Excluse jobs with these terms
timeNow = datetime.datetime.now()
formattedTime = timeNow.strftime("%d") + "-" + timeNow.strftime("%b") + "-" + timeNow.strftime("%Y")
fileName = 'jobs-' + formattedTime + '.csv'

ratingInfo = []
jobDict = []

URLList = getSearchURLs(inputList, filterTerms)
for jobURL in URLList:
    extractJobs(jobURL)

downloadCSV(jobDict, fileName)
