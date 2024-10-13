#################################################################
#               Author: Ismael Maurice                          #
#               Language: Python                                #
#               Projet: Gitlab Clone                            #
#               Version: V1                                     #
#               File: main.py                                   #
#################################################################

"""
    The main package which will load the env variable to clone the gihub repositories.
"""
import warnings
warnings.filterwarnings("ignore")

# Import the modules
import pyfiglet
import os
from helpers import *
import constants
import logging

# Init the date
import datetime
now = datetime.datetime.now()
displayDate = now.strftime("%Y-%m-%d")
# Configure the logging
if not os.path.exists('logs') or not os.path.isdir('logs'):
    os.makedirs('logs')
logging.basicConfig(filename=f'logs/{displayDate}.log', format='%(levelname)s:%(message)s', filemode='w', level=logging.DEBUG)

# Display the application logo
ASCII_art = pyfiglet.figlet_format(constants.APP_NAME + f'\n{displayDate}', justify="center")
print(ASCII_art)
message = constants.APP_NAME + f' - {now.strftime("%Y-%m-%d")}'
logging.debug(message)

# Init start time
import time
startTime = time.time()

try:
    # Import the env
    from dotenv import dotenv_values

    config = dotenv_values(".env")

    # Verification of config
    verificationConfig(config=config)

    # Set the constants values
    TOKEN = config["TOKEN"]
    FOLDER = config["FOLDER"]
    BASE_URL = f"{config['PROTOCOL']}://{config['DOMAIN']}/api/v4"
    USERNAME = config["USERNAME"]

    # Init the metric
    metric = {
        "success": 0,
        "failed": 0,
        "update": 0,
        "new": 0
    }
    # Define the list of repo list which has failed to be cloned
    repoListFailed = []
    # Define the list of repo list which branches have failed to be cloned
    repoListPartial = []
    # Define the list of failed update forked
    repoForkFailed = []

    # Display the repository list
    responseRepo = getRepositoryData(baseUrl=BASE_URL, token=TOKEN)
    message = f"{len(responseRepo)} repositories found for {USERNAME} and are:"
    logMessage(message=message, logType="info")
    for repo in responseRepo:
        message = f"{repo['name']}"
        logMessage(message=message, logType="info", addSeparator=False)

    # Clone the repositories
    import os
    if not os.path.isdir(FOLDER):
        os.makedirs(FOLDER)
    for repo in responseRepo:
        repoName = repo["name"]
        # Create the result folder
        resultFolder = f"{FOLDER}/{repoName.replace(' ', '-')}"
        if not os.path.isdir(resultFolder):
            os.makedirs(resultFolder)
            metric["new"] += 1
            try:
                cloneUrl = getRepoCloneUrl(url=repo["url"], username=USERNAME, token=TOKEN)
                cloneCommand = f"git clone {cloneUrl} {resultFolder}"
                os.system(cloneCommand)
                metric["success"] += 1
            except:
                metric["failed"] += 1
                repoListFailed.append(repoName)
        else:
            metric["update"] += 1

        # Update if it fork
        if repo["isFork"]:
            try:
                repoSourceUrl = repo["forkData"]["http_url_to_repo"]
                os.chdir(resultFolder)
                os.system(f"git remote add upstream {repoSourceUrl}")
                os.system(f"git checkout {repo['defaultBranch']}")
                os.system("git fetch upstream")
                os.system(f"git pull upstream {repo['defaultBranch']}")
                os.system(f"git push origin {repo['defaultBranch']}")
            except:
                repoForkFailed.append(repoName)

        # Loop to update each branch
        try:
            os.chdir(resultFolder)
            defaultBranch = repo["defaultBranch"]
            for branchName in repo["branches"]:
                if branchName != defaultBranch:
                    # Checkout branch
                    checkoutCommand = f"git fetch origin {branchName} && git checkout {branchName}"
                    os.system(checkoutCommand)
                    # Pull all code from branch
                    os.system("git pull")
                    # Apply defense
                    updateCommitAndLFS()
            # Move to default branch
            os.system(f"git checkout {defaultBranch}")
            # Pull all code from branch
            os.system("git pull")
            # Apply defense
            updateCommitAndLFS()
        except:
            repoListPartial.append(repoName)

    # Display the result of metric
    message = f"The summary of actions are:"
    logMessage(message=message, logType="info")
    message = f"Number of new repository clones: {metric['new']}"
    logMessage(message=message, logType="info", addSeparator=False)
    message = f"Number of repository updates: {metric['update']}"
    logMessage(message=message, logType="info", addSeparator=False)
    message = f"Number of failures: {metric['failed']}"
    logMessage(message=message, logType="info", addSeparator=False)
    message = f"Number of successes: {metric['success']}"
    logMessage(message=message, logType="info", addSeparator=False)
    if len(repoForkFailed) > 0:
        message = f"The list of {len(repoForkFailed)} fork {'repository' if len(repoForkFailed) < 2 else 'repositories'} which failed to be synchronized:"
        logMessage(message=message, logType="info")
        for repo in repoForkFailed:
            logMessage(message=repo, logType="info", addSeparator=False)
        logMessage(message="\n", logType="info", addSeparator=False)
    if len(repoListFailed) > 0:
        message = f"The list of {len(repoListFailed)} {'repository which' if len(repoListFailed) < 2 else 'repositories which are failed'} failed to be cloned:"
        logMessage(message=message, logType="info")
        for repo in repoListFailed:
            logMessage(message=repo, logType="info", addSeparator=False)
        logMessage(message="\n", logType="info", addSeparator=False)
    if len(repoListPartial) > 0:
        message = f"The list of {len(repoListPartial)} {'repository' if len(repoListPartial) < 2 else 'repositories'} which failed to be updated:"
        logMessage(message=message, logType="info")
        for repo in repoListPartial:
            logMessage(message=repo, logType="info", addSeparator=False)
        logMessage(message="\n", logType="info", addSeparator=False)


except Exception as err:
    message = f"Unexpected {err}, {type(err)}"
    logMessage(message=message, logType="error")

finally:
    # Show analyse time
    endTime = time.time()
    message = f"This programme takes: {getSecondsConvertion(endTime-startTime)}"
    logMessage(message=message, logType="info")