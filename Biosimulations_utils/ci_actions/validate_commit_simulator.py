""" Utilies for CI workflows for reviewing and committing simulators to the BioSimulators registry

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-10-20
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

import io
import os
import requests
import simplejson.errors
import yamldown


class ValidateCommitSimulatorCiActions(object):
    ISSUE_ENDPOINT = 'https://api.github.com/repos/biosimulators/Biosimulators/issues/{}'
    ISSUE_COMMENTS_ENDPOINT = 'https://api.github.com/repos/biosimulators/Biosimulators/issues/{}/comments'
    ISSUE_LABELS_ENDPOINT = 'https://api.github.com/repos/biosimulators/Biosimulators/issues/{}/labels'
    BIOSIMULATORS_ENDPOINT = 'https://api.biosimulators.org/simulators'

    def validate(self):
        """ Validate a submission of simulator """

        # retrieve issue
        issue_number = os.getenv('ISSUE_NUMBER')
        issue = self.get_issue()
        submitter = issue['user']['login']
        self.add_comment_to_issue(('Thank you @{} for your submission to the BioSimulators registry of containerized simulation tools! '
                                   'We will review your submission and discuss any issues here.').format(submitter))

        # parse submision
        submisssion = self.get_submission(issue)
        specUrl = submisssion['specificationsUrl']

        # validate specifications
        specs = self.get_specs(specUrl)
        self.add_comment_to_issue('The specifications of your simulator is valid!')

        # TODO: validate container
        self.add_comment_to_issue('Your containerized simulator is valid!')

        # label issue as `validated`
        auth = self.get_gh_auth()
        response = requests.post(
            self.ISSUE_LABELS_ENDPOINT.format(issue_number), 
            auth=auth, 
            json={'labels': ['Validated']})
        response.raise_for_status()

        # post success message
        self.add_comment_to_issue(
            'A member of the BioSimulators team will review your submission before final committment to the registry.')

    def commit(self):
        """ Commit a simulator (id and version) to the BioSimulators registry """

        issue_number = os.getenv('ISSUE_NUMBER')
        issue = self.get_issue()
        submisssion = self.get_submission(issue)
        specUrl = submisssion['specificationsUrl']
        specs = self.get_specs(specUrl)

        # TODO: commit submission to BioSimulators database
        # requests.post(BIOSIMULATORS_ENDPOINT, data=specs)

        # post success message
        self.add_comment_to_issue(
            'Your submission was committed to the BioSimulators registry. Thank you!')

        # close issue
        auth = self.get_gh_auth()
        response = requests.patch(
            self.ISSUE_ENDPOINT.format(issue_number),
            auth=auth,
            json={'state': 'closed'})
        response.raise_for_status()

    def get_issue(self):
        """ Get the properties of the GitHub issue for the submission

        Returns:
            :obj:`dict`: properties of the GitHub issue for the submission
        """
        issue_number = os.getenv('ISSUE_NUMBER')
        auth = self.get_gh_auth()
        response = requests.get(self.ISSUE_ENDPOINT.format(issue_number), auth=auth)
        response.raise_for_status()
        return response.json()

    def get_submission(self, issue):
        """ Get the properties of the submission

        Args:
           issue (:obj:`dict`): properties of the GitHub issue for the submission 

        Returns:
            :obj:`dict`: dictionary with `simulator`, `version`, and `specificationsUrl` keys
        """
        body = io.StringIO(issue['body'].replace('\r', ''))
        submission, _ = yamldown.load(body)

        simulator = submission.get('name', None) or None
        version = submission.get('version', None) or None
        specUrl = submission.get('specificationsUrl', None) or None

        # validate properties of submission
        errors = []
        if not simulator:
            errors.append('A simulator name must be provided.')
        if not version:
            errors.append('A simulator version must be provided.')
        if not specUrl:
            errors.append('A URL for the specifications of the simulator must be provided.')
        if errors:
            comment = ('Your simulator could not be verified. '
                       'Please edit the first block of this issue to re-initiate this validation.\n- ') + '\n- '.join(errors)
            self.add_error_comment_to_issue(comment)

        return submission

    def get_specs(self, url):
        """ Get the specifications of the simulator
        Args:
            url (:obj:`str`): URL for the specifications of the simulator

        Returns:
            :obj:`dict`: specifications of the simulator
        """
        response = requests.get(url)

        try:
            response.raise_for_status()
        except requests.RequestException as error:
            self.add_error_comment_to_issue(
                ('Your simulator could not be verified because we could not retrieve the specifications from {} ({}: {}). '
                    'Once the issue is fixed, edit the first block of this issue to re-initiate this validation.').format(
                    url, response.status_code, response.reason)
            )

        try:
            return response.json()
        except simplejson.errors.JSONDecodeError as error:
            self.add_error_comment_to_issue(
                ('Your simulator code not be verified because the specifications are not valid JSON:\n\n  {}\n\n'
                    'Once the issue is fixed, edit the first block of this issue to re-initiate this validation.').format(str(error)))

        # TODO: validate specifications with BioSimulators API

    def get_gh_auth(self):
        """ Get authorization for GitHub

        Returns:
            :obj:`dict`: authorization for GitHub
        """
        user = os.getenv('GH_ISSUES_USER')
        access_token = os.getenv('GH_ISSUES_ACCESS_TOKEN')
        return (user, access_token)

    def add_error_comment_to_issue(self, comment):
        """ Post an error to the GitHub issue

        Args:
            comment (:obj:`str`): comment

        Raises:
            :obj:`ValueError`
        """
        self.add_comment_to_issue(''.join([
            '```diff\n',
            '- ' + comment.rstrip().replace('\n', '\n- ') + '\n',
            '```\n',
        ]))
        raise ValueError(comment)

    def add_comment_to_issue(self, comment):
        """ Post a comment to the GitHub issue

        Args:
            comment (:obj:`str`): comment
        """
        issue_number = os.getenv('ISSUE_NUMBER')
        auth = self.get_gh_auth()

        response = requests.post(
            self.ISSUE_COMMENTS_ENDPOINT.format(issue_number),
            headers={'accept': 'application/vnd.github.v3+json'},
            auth=auth,
            json={'body': comment})
        response.raise_for_status()