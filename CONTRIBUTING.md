## How to contribute to this ansible role
### Install 'pre-commit' dependency

To enable automatic checks (like code linting) beforey each commit it is advised to install ***pre-commit***:

Install it to your environment: 

`~/ansible_nextcloud$ pip install pre-commit` (for more options see [here](https://pre-commit.com/#installation))

Enable pre-commit within the repo: 

`~/ansible_nextcloud$ pre-commit install`

(Optional) Run complete check once: 

`~/ansible_nextcloud$ pre-commit run --all-files`