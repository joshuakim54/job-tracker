Hi my name is Josh. I built a job tracker specifically for software engineering but am tweaking it so my girlfriend and other friends can use it for various fields. I also recommend using https://chromewebstore.google.com/detail/simplify-copilot-autofill/pbanhockgagggenencehbnadejlgchfc just to make applying to jobs a bit easier. I built this because I felt like LinkedIn had a lot of ghost listings and old job listings. This pulls directly from a companies career website. 

## Streamlit GUI

The browser-based search interface is in `app.py`. It lets you search selected company career sites with custom role, location, and required terms, plus selectable experience levels: internships, new grads, experienced, and seniors. It supports Greenhouse, Lever, Workday, and iCIMS career sites.

Run it locally with:

```bash
pip install -r requirements.txt
streamlit run app.py
```

To publish it, push the repository to GitHub and deploy it from [Streamlit Community Cloud](https://share.streamlit.io/). Select `app.py` as the main file and `requirements.txt` will be installed automatically. GitHub Pages cannot run this Python app.

The experience selector maps titles automatically. New-grad roles include common markers such as `early career`, `associate software engineer`, `software engineer I`, and `software engineer 1`. Senior roles include titles containing `senior`, `staff`, `principal`, `lead`, `distinguished`, or `architect`.

> TODO: Restore IBM and Salesforce after their current career-site API paths are verified.
