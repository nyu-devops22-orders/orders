# NYU DevOps (SP22) - ORDERS Team
[![CI Build](https://github.com/nyu-devops22-orders/orders/actions/workflows/workflow.yml/badge.svg)](https://github.com/nyu-devops22-orders/orders/actions/workflows/workflow.yml)   [![BDD Build](https://github.com/nyu-devops22-orders/orders/actions/workflows/bdd.yml/badge.svg)](https://github.com/nyu-devops22-orders/orders/actions/workflows/bdd.yml)  [![codecov](https://codecov.io/gh/nyu-devops22-orders/orders/branch/main/graph/badge.svg?token=NH44EBYAS1)](https://codecov.io/gh/nyu-devops22-orders/orders)

### Current Project Status
```
# | Description                              | Status     
---|------------------------------------------|------------
 1 | Add Query And Action Routes              | Complete   
 2 | Add Continuous Integration               | Complete   
 3 | Deploy To Cloud                          | Complete   
 4 | Implement A Ui W/ Automated Testing      | Complete   
 5 | Refactor Using Flask-Restx And Swagger   | Incomplete 
 6 | Build An Automated Ci/cd Devops Pipeline | Incomplete 
```
## Installation
1. Navigate to your local DevOps folder
2. Clone the repo
```python
$ git clone https://github.com/nyu-devops22-orders/orders.git
```
3. Change directory (cd)

```python
 $ cd orders
```
4. Open VSCode in current directory
```python
 $ code . 
```
5. Open in Container - ***Make sure docker is running or you won't be able to open in container***
7. Pull up-to-date code from GitHub
```python
$ git pull
```

## Running the Service
```python
# Run unit tests
$ nosetests

# Start honcho
$ honcho start

# Run behave tests
$ behave
```
## Interacting with the WebUI
- Navigate to <a href="http://localhost:8080">localhost:8080</a>
- Try various actions
  - Add new order w/ new customer
  - Add new order w/ existing customer
  - Delete order
  - Update an order's information
  - Cancel an order
  - Search for an order by: Customer, Date, Status


## Utility

#### Look into postgresql db 
1. Launch Git Bash (Windows) or Terminal (MacOS / Linux)
```python
# Run docker container
docker exec -it orders_devcontainer_postgres_1 bash

# Create user postgres
$ psql -U postgres

# Connect with postgres user account
\c postgres

# List tables
$ \dt

# Query table
$ select * from public.order;
```

## **M1 MAC USERS**
The package psycopg2 doesn't work on IBM Cloud Foundry and is replaced with psycopg2-binary. Unfortunately, this package breaks on M1 Macs, so users will need to\ modify the ***requirements.txt*** by commenting out the binary package and uncommenting the normal release package. 
<br>
<br>
From
```python
psycopg2-binary==2.9.3
# psycopg2==2.9.3

```
To
```python
# psycopg2-binary==2.9.3
psycopg2==2.9.3
```

## Important Links
<a href="https://app.zenhub.com/workspaces/devops22---orders-6215269860583f0012cc1733/board">ZenHub Board</a>
<br>
<a href="https://cloud.ibm.com/devops/pipelines/feab792f-5e52-4959-a71b-0dbb1abb0d70?env_id=ibm:yp:us-south">IBM Cloud Pipeline</a>



