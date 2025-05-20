# Exotics Disk Space Usage

This repository contains a collection of scripts to be run regularly via CI pipelines, making it easier to keep track of the usage of the disk space available to the Exotics group.

Separate scripts are used to monitor the two storage resources: 
- [eos.py](eos.py) for everything related to `/eos/atlas/atlascerngroupdisk/phys-exotics`
- [gridspace.py](gridspace.py) for everything related to storage on `CERN-PROD_PHYS-EXOTICS` and `TOKYO-LCG2_PHYS-EXOTICS`

The repository is mirrored to [Github](https://github.com/vaustrup/ExoticsDiskspaceUsage), from where the data is fetched in the [Exotics Storage Documenation](https://gitlab.cern.ch/atlas-phys/exot/docs/exotics/-/blob/master/docs/ExoStorageDocs.md?ref_type=heads&plain=1#L272), such that the numbers in the documentation are automatically up-to-date. (This workaround is necessary, because, unfortunately, fetching directly from Gitlab does not work.)

## CI pipeline setup

The workflow is defined in [.gitlab-ci.yml](.gitlab-ci.yml).
The scripts [eos.py](eos.py) and [gridspace.py](gridspace.py) are run daily at 12am CERN time, to update the data in `reports/`. The `*.csv` files are automatically converted into TWiki format in order to show the data on the Exotics Disk Space TWiki page.
In addition, once a week a short summary in PDF format is compiled and is sent to the Exotics disk space manager via email. This is done using the [send_weekly_report.py](send_weekly_report.py) script.
In order for the CI to work, the following CI/CD variables have to be set in the Gitlab repository's settings:
- ACCESS_TOKEN (for Gitlab)
- PASSWORD (of ExoticsDiskspaceWatcher service account, for lxplus)
- USERCERT (these are the grid credentials, base64-encoded, currently of the Exotics disk space manager, but for security reasons hopefully credentials can be made available for the service account itself soon)
- USERKEY (these are the grid credentials, base64-encoded, currently of the Exotics disk space manager, but for security reasons hopefully credentials can be made available for the service account itself soon)

## eos.py

This script is called daily in the [CI workflow](.gitlab-ci.yml). The available options are

```
  -h, --help            show this help message and exit
  -s SUBGROUPS [SUBGROUPS ...], --subgroups SUBGROUPS [SUBGROUPS ...]
                        Specify subgroups to check.
  --report-in-gitlab    Automatically report findings (missing information, ...) in Gitlab issue.
```

where `SUBGROUPS` is a list of subgroups to check and defaults to `["ccs", "cdm", "hqt", "jdm", "jmx", "lpx", "lup", "ueh"]` as defined in [constants.py](constants.py).
Similarly, `--report-in-gitlab` is meant to be used in the CI pipeline only. By setting this flag, an issue is created in Gitlab in case of missing information (see below) and assigned to the Exotics disk space manager. For this, the Gitlab user ID is set in [constants.py](constants.py).

The script calls the [EOS Analyser](analysers/eosanalyser.py) which loops through the directories in a given subgroup's folder and tallies the numbers of files as well as the disk space required. For the given subgroup, the data in `reports/<subgroup>.csv` is updated accordingly, including the analysis' Glance code.
Analysis folders are matched to Glance codes using the look-up table in [glance_codes.csv](glance_codes.csv). The format of the table is "\<FolderName\> \<GlanceCode1,GlanceCode2,...\>". If, during the daily CI pipeline, a folder without matching Glance code is detected, an issue is created automatically (using the `--report-in-gitlab` flag mentioned above) in [https://gitlab.cern.ch/vaustrup/exoticsdiskspaceusage](https://gitlab.cern.ch/vaustrup/exoticsdiskspaceusage) and assigned to the Exotics disk space manager.

## gridspace.py

This script is called daily in the [CI workflow](.gitlab-ci.yml). The available options are

```
  -h, --help            show this help message and exit
  --rse {CERN-PROD_PHYS-EXOTICS,TOKYO-LCG2_PHYS-EXOTICS}
                        RSE to check
```

where RSE specifies the RSE to check and can be set to either `CERN-PROD_PHYS-EXOTICS` (default) or to `TOKYO-LCG2_PHYS-EXOTICS`.
The script calls the [Gridspace Analyser](analysers/gridspaceanalyser.py).
A [look-up table](lookup_table.csv) is used to match dataset names to analysis teams.

## send_weekly_report.py

This script is called once per week in the [CI workflow](.gitlab-ci.yml). It compiles a short summary of the state of the Exotics disk space. If called from within the CERN network (e.g. in the CI pipeline), an email is sent to the Exotics disk space manager, with the report in PDF format as attachment. If you also want to receive this report, please add yourself to the list of subscribers [here](https://gitlab.cern.ch/vaustrup/exoticsdiskspaceusage/-/blob/main/helpers/constants.py?ref_type=heads#L22).