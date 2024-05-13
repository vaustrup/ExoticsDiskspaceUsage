import os

import gitlab

from helpers.logger import log


def get_issue(project, title="", description=""):
    """
    Retrieve an already open issue, or create a new one if no open issue is found
    Arguments:
        project -> Gitlab project instance
        title: str -> title of the issue to retrieve
        description: str -> description to add to the issue if it needs to be created
    """
    # only look for open issues created by the exowatch Gitlab account
    # find the ID in the Gitlab account settings
    issues = project.issues.list(state="opened", author_id="31566")
    # then filter by title
    for issue in issues:
        if issue.title == title: 
            return issue
    # if no open issue exists, open a new one
    log.info(f"Opening new issue with title {title}.")
    issue = project.issues.create({"title": title, "description": description})
    return issue

def get_project():
    """
    Retrieve Gitlab project instance using the private ACCESS_TOKEN stored in the project's CI/CD variables
    """
    gl = gitlab.Gitlab(f'https://{os.getenv("CI_SERVER_HOST")}', private_token=os.getenv('ACCESS_TOKEN'))
    # make sure the exowatch gitlab account is added as member to the project
    project_id = os.getenv('CI_PROJECT_ID')
    log.info(f"Retrieving project with ID {project_id}.")
    project = gl.projects.get(project_id)
    return project

def report_missing_glance_code(analyses_without_glance: list[str]) -> None:
    """
    Report analysis directories not listed in glance_codes.csv in an issue on the ExoticsDiskspaceUsage Gitlab project

    Arguments:
        analyses_without_glance: list[str] -> list of analyses for which no corresponding Glance code has been found
    """
    
    # no need to worry about anything if there are no analyses without Glance information
    if analyses_without_glance == []:
        log.info("Found no directories without Glance information.")
        return

    # otherwise, look for the issue listing all directories for which information is missing
    project = get_project()
    title = "Automatic Report: Analysis directories without Glance information"
    description = f"""
No information on the Glance code is available in [glance_codes.csv](https://{os.getenv("CI_SERVER_HOST")}/{os.getenv("CI_PROJECT_PATH")}/-/blob/main/glance_codes.csv?ref_type=heads&plain=1) for the following analysis directories:

"""
    issue = get_issue(project, title=title, description=description)

    # make sure the issue is correctly assigned to the Exotics disk space manager
    # the user ID can be found in the user's gitlab profile
    assignee_id = 6032
    if issue.assignee is None or issue.assignee["id"] != assignee_id:
        log.info(f"Assigning issue to user with ID {assignee_id}.")
        issue.assignee_id = assignee_id
        issue.save()

    description = issue.description
    # add a todo item for each new directory
    for analysis in analyses_without_glance:
        if analysis not in description:
            log.info(f"{analysis} not yet in issue, adding it now.")
            description += f"\n - [ ] {analysis}"

    # only update the issue if new information has been added
    if description != issue.description:
        log.info("Updating issue description.")
        issue.description = description
        issue.save()
