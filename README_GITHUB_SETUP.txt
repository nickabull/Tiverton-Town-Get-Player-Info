TIVERTON TOWN FIXTURE BOARD - ONLINE / NO LOCAL COMMANDS
========================================================

WHAT THIS VERSION DOES
----------------------
This version is designed for GitHub Pages + GitHub Actions.
Nothing needs to run on your work laptop.

GitHub's own servers will:
  1. Read Tivvy Archive / Tiverton Town / Football Web Pages.
  2. Rebuild data.json and data.js.
  3. Rebuild the coloured Excel matrix.
  4. Publish the updated webpage.

It automatically runs at 07:30 and 23:30 Europe/London every day.
You can also run it manually from GitHub's Actions tab.

ONE-TIME SETUP
--------------
1. Sign in to GitHub and create a new repository, for example:
      tiverton-fixtures

   A PUBLIC repository is the simplest option for GitHub Pages on GitHub Free.
   Do not put passwords, work information or anything private in this repository.

2. Upload ALL files and folders from this ZIP into the repository root.
   Important: upload the hidden .github folder too.

3. Commit the files to the main branch.

4. In the repository go to:
      Settings > Pages

5. Under "Build and deployment" set Source to:
      GitHub Actions

6. Open the Actions tab. Choose:
      Update Tiverton fixtures and publish
   Then click "Run workflow" once.

When it finishes, GitHub will show the Pages website address.
Bookmark that address on your laptop/iPhone.

NORMAL USE
----------
You do not need to download this ZIP again and you do not need to run a .cmd or
PowerShell file on your computer.

Just open the GitHub Pages bookmark. The site updates itself twice daily.
The "Download Excel" button downloads the latest generated matrix.

AFTER A MATCH
-------------
The 23:30 run should normally be late enough for a match report. If the club
publishes a report later, either wait for the 07:30 run or open GitHub > Actions
and click "Run workflow". That action runs on GitHub, not on your work laptop.

FILES
-----
index.html                          The webpage
Update Tiverton Fixtures.cloud.ps1 Cloud scraper; runs only on GitHub
                                      Actions, not on your laptop
generate_excel.py                   Creates the downloadable Excel matrix
data.json / data.js                 Current fixture data
.github/workflows/...               Automatic update/deploy instructions

SECURITY NOTE
-------------
This package intentionally contains no .cmd launcher. The PowerShell file is
there only because GitHub's Windows runner executes it remotely. You should not
need to run it locally.
