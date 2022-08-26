# event-pages-preview

Simplified clone of event pages with database integration as infrastructure for mentors/hosts to preview & submit their event sites.

<img src = images/form1.png width="350" height="auto">
<img src = images/form3.png width="350" height="auto">
<img src = images/preview.png width="350" height="auto">

## Development notes
### Deployment
Deployed app can be accessed at http://tpeventpageform.org/

This is a "dynamic" app that communicates with the database live (unlike `analytics-dash-with-events`, which is static and has data updated periodically). App updates will automatically re-deploy to Elastic Beanstalk on every push to the master branch via the Github actions workflow in `.github/workflows/main.yml`. Relevant updates to dependencies (like `tech_team_database`) will require manual re-run of the `deploy` workflow to update the deployed version, since the workflow checks out the latest version for deployment. Any files in the repository that should not be deployed should be added to `.ebignore`.

### Running locally
Because Elastic Beanstalk expects the flask app to be named `application`, set the `FLASK_APP` environment variable to `application.py` before running Flask locally. To run in debug mode locally, set the environment variable instead of using the parameter in `application.run()` so that the production app is not in debug mode. For example, on Linux:
```
$ setenv FLASK_DEBUG=1
$ setenv FLASK_APP=application.py
$ flask run
```

All installation dependencies required in the deployed app must be included in `requirements.txt`. If you are using a virtual environment, you can install the relevant requirements locally from `requirements.txt` with `pip3 install -r requirements.txt` or output the installed packages in your virtual environment into `requirements.txt` with `pip3 freeze > requirements.txt`. You will also need a local copy of `tech_team_database`.

### Development practices
Include Jinja html templates in the `templates` subdirectory, and all other static files (images, attachments, CSS files, JS files, etc.) that are part of the app in `static`. The top level `images` directory is only for images used in this README. When referencing other files from a template, do not use the relative path, as this may cause problems for shared template bases if templates are reorganized into different subfolders. Instead, use `url_for`. For example, use
```
<link rel="stylesheet" href="{{ url_for('static', filename='css/form.css') }}">
```
instead of
```
<link rel="stylesheet" href="../static/css/form.css') }}">
```