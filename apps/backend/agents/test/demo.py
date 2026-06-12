# demo testcase
from locale import currency

supplier = None
currencyr_base = 'INR'
currency_company = 'USD'
supplier_currency = "EUR"

if not supplier:
    supplier_currency = currency_company

if supplier:
    supplier_currency = supplier_currency


# demo testcase
from locale import currency

supplier = None
currencyr_base = 'INR'
currency_company = 'USD'
supplier_currency = "EUR"

if not supplier:
    supplier_currency = currency_company

if supplier:
    supplier_currency = supplier_currency


from fastapi import FastAPI
from pr_reviewer_agent.apps.code_reviewer.routers.github import router as github

app = FastAPI()

app.include_router(github, prefix='/api')