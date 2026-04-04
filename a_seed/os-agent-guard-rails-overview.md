# OS-Agent RPA Guard Rails Plan and Testing Scenarios

## Project Overview

OS-Agent RPA Guard Rails is an OpenClaw plugin and skill that provides a guard rails for OpenClaw tasks and processes so it can be used in Robotic Process Automation (RPA) for business automation, without any errors or exceptions.

Initially, the User will have an existing database or service with a known schema that they want to setup business rules for, as guard rails for automation processing. Thus we build two dummy applications, one based on a postgres/sql database, and one based on a REST API service, both filled with data to demonstrate the capability of the guard rails, each documented through a scenario plan, describing the set of rules and tasks to demonstrate the power of the guard rails for that scenario.

Later on, the User will be able to setup business rules for new tasks or services, without any coding or configuration. 

## Background

Many apps are based on databases that do not suit agents, they do not enable meta-queiries to identify what types are in the database, they do not include business rules, and for many reasons cannot act as agent guard rails. Further, API services also do not enable business rules. They can only be content the agent reads. This guardrails project is based on ideas in the book described in the directory agent_book.

## Aims

The aim is to build an RPA plugin/skill for OpenClaw to provide:

1. A simple user interface to setup rules on applications and API's  to guarantee task effectiveness by using MCP queries on a shadow TypeDB database to enforce agent rules for each data record they process
2. A TypeDB Promise Graph MCP Server to enable advanced agent orchestration, so that task promises are kept, and results are recorded in the TypeDB database for every task, so that the user can always be sure that the task will be completed using the rules and data, and the results are recorded in the TypeDB database.
3. A simple user interface to setup agents to run RPA tasks with our plugin/skill to process the tasks, where the agent will use the MCP server to check the logic for every data record and issue/vote on every Promise needed for the task.
4. A simple user interface to review the results of the tasks, and to appeal or override the decisions of the guard rails. The effectiveness of any task or agent can be clarified through a simple dashboard of the results of the tasks, and the effectiveness of the guard rails.

In order to test this OS-Agent RPA Guard Rails plugin/skill, we need to build two detailed scenarios to tell the story, each with two parts, firstly a detailed plan for a complete mini app for each scenario, each filled with a few hundred rows of generated data appropriate for the scenario. Secondly a separate scenario plan outlining how this RPA plugin/skill enables users to:

1. Connect to this dummy database or API, 
2. Set up rules to suit their scenario, then 
3. Setup RPA tasks that use the rules,  
4. Setup and schedule tasks and then 
5. Evaluate the results, examine the agent statistics of the promises, and the effectiveness of the guard rails.

Ideally, these guaranteed results are performed on domains and functions of real consequences (medicine and finances), life or death stuff, so the scenarios should also include a quick, medium, and longer demo plan to demonstrate the capability to an investor. Also, the scenarios should be designed to be performed on a local machine (WSL & Docker Desktop), so that the investor can see the results of the tasks, and the effectiveness of the guard rails.

## Deliverables

**STAGE 1: Documentation** In the first stage, we need to deliver the following:

1. A detailed plan of how to implement the plugin/skill in OpenClaw, and document it in the directory (plan\rpa_guidelines_plan\PLAN.md). The plan needs to be sufficient to allow you to flawlessly implement the plugin/skill in OpenClaw, and to demonstrate the capability to an investor. Include diagrams of the user journey needed to register a new application/API service, setup rules, schedule tasks, and review the results of the tasks. Include all of the information needed to convert the plan into github issues and develop the code in the correct order. Include a full testing approach to ensure the plugin/skill works correctly.
2. A detailed plan to build a complete mini app for each scenario and run it in docker desktop(plan\medical_app_scenario\PLAN.md and plan\financial_planner_api_scenario\PLAN.md), each filled with a few hundred rows of generated data appropriate for both the sql and the api scenario. Make sure the web iFrame user interface for each mini app contains all of the data views and forms necessary to use the app, and that the data is loaded and displayed correctly.
3. A detailed plan for each scenario (plan\medical_app_scenario\SCENARIO.md and plan\financial_planner_api_scenario\SCENARIO.md) to describe how this RPA plugin/skill enables users to:
   - Connect to the dummy database or API service, 
   - Set up rules to suit their scenario, then 
   - Setup RPA tasks that use the rules,  
   - Setup and schedule tasks and then 
   - Evaluate the results, examine the agent statistics of the promises, and the effectiveness of the guard rails.
4. A detailed plan to demonstrate this capability to an investor, including a 1-min demo, a 5-min demo and a 20-min demo plan (plan\financial_planner_api_scenario\DEMO.md and plan\medical_app_scenario\DEMO.md)
5. A README.md file in the root directory of the repository to describe the project, and link to the plan and scenario documents, and an update to the project README.md to include the new plugin/skill.

**STAGE 2: Implementation** Once these documentation and scenario plans are complete, we can move to implementation:

1. Implement the medical app scenario, load the data and test the user interface (code\medical_app_scenario)
2. Implement the financial planner api scenario, load the data and test the user interface (code\financial_planner_api_scenario)
3. Implement the RPA plugin/skill in OpenClaw, and test it with the built in testing framework (code\rpa_plugin_skill)
4. I will then manually run through the medical app scenario doc to create new rules, setup tasks, schedule them and review their accuracy and effectiveness using the plugin/skill user interface (plan\medical_app_scenario\SCENARIO.md)
5. I will then manually run through the financial planner api scenario doc to create new rules, setup tasks, schedule them and review their accuracy and effectiveness using the plugin/skill user interface (plan\financial_planner_api_scenario\SCENARIO.md)
6. I will then manually demonstrate the capability to an investor, including a 1-min demo, a 5-min demo and a 20-min demo plan using the user interface of the plugin/skill (plan\financial_planner_api_scenario\DEMO.md and plan\medical_app_scenario\DEMO.md)

## User Benefits

For the user, the plugin provides an RPA rules user interface on a localhost port, so they can construct a series of business rules they wish to apply to ab existing database or service, and store them locally in TypeDB. The user can then setup agents to run tasks using our plugin/skill to process the permissions/logic for each task, and coordinate through promises by interacting with our dynamically generated MCP server. In the background, OS Agent RPA Guard Rails will dynamically make schemas in TypeDB to shadow existing databases and API services, including their key ids, initially based on transpiling an SQL schema into a TypeQL schema, or transpiling Swagger documentation into a TypeQL schema. Based on the rules put forward, OS Agent RPA Guard Rails will auto-generate SQL or API commands to extract the data needed for the shadow system to make decisions for the task, and generate the TypeQL statements needed to insert this shadow data into TypeDB. Further, agents will coordinate and record their results on every task using Promise contracts. Every decision and outcome must be accounted for, and available for users to review. 100% accurate RPA, with full audit trail, is a powerful feature, and this plugin/skill will enable it.

## Basic Flow of the Plugin/Skill

1. **Register:** The user registers a new application or API service in the user Interface, 
2. **Background:** In the background, the plugin/skill will request the SQL schema or REST API Swagger documentation, and use it to dynamically generate a TypeQL schema, create a new database, and load the schema for the shadow system, ready for data
3. **Rules:** The user enters the rules area for that registered application or API service, and creates and manages rules in a rule management interface. The default view is the list of rules. From there one can edit an existing rule, or create a new rule on a rule composer page, where the natural language for the rules is entered on the left side of the ui, and the Horn Logic IF, Then ELSE rules and diagrams are displayed on the right hand side of the ui in the Logic viewer tab.
4. **Background:** In the background, this list of If Then else rules are converted into functions in the TypeQL declartive data language, appended to the schema, which then updates the shadow system. The user can view the TypeQL functions in the TypeQL viewer tab on the right hand side of the ui. At this stage, the database still has no data, only schema
5. **MCP Server:** An MCP server is dynamicallygenerated from the new TypeQL functions, and the Promise Graph MCP Server enables the agent to check the logic for evey data record necessary for the task
6. **Task:** After the rules are setup, the user gives an automation task to an agent to process. An RPA automation user interface is provided to the user to setup tasks, schedule tasks, review the results of the tasks, and to appeal or override the decisions of the guard rails 
7. **Background:** In the background, the plugin/skill will generate the SQL or API commands to extract the data needed for the shadow system to make decisions for the task, and generate the TypeQL statements needed to insert this shadow data into TypeDB.
8. **Task:** The agent will use the MCP server to check the logic for every data record necessary for the task, and issue/vote on every Promise needed for the task.
9. **Background:** A TypeDB database is used to contain the results of all rpa agent tasks, so that the agent issues a promise to the user on each execution that the task will be completed, and the user can review the results of the tasks in the logical database. If other agents are required to judge the effectiveness of promises, then build that in too. Effectively a detailed record of the agents progress and results on every task can always be traced back to the original database and rules that were applied.
10. **Review:** The user can review the results of the tasks in a user interface, and the effectiveness of the guard rails in a dashboard. 
11. **Review:** Ideally, using the two application scenarios we can test agents without guardrails and agents with guard rails on the same set of rpa tasks , and compare the results.

## Plan of the OS Agent RPA Guard Rails Plugin/Skill

First you need to build a detailed plan of how to implement the plugin/skill in OpenClaw, and document it in the directory (plan\rpa_guidelines_plan). The plan needs to be sufficient to allow you to flawlessly implement the plugin/skill in OpenClaw, and to demonstrate the capability to an investor. Include diagrams of the user journey needed to register a new application/API service, setup rules, schedule tasks, and review the results of the tasks. Include all of the information needed to convert the plan into github issues and develop the code in the correct order. Include a full testing approach to ensure the plugin/skill works correctly.

Use the complete Promise Graph schema and application examples from this page https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/17-promise-graphs.md to help you understand the concept of Promise Graphs, and how to use them to coordinate agents and tasks. All of the other steps ion the flow need to be devised by yourself and correctly planned out.

We can debug, improve and show off the plugin/skill to an investor by using the scenarios below, and demonstrating the capability to an investor.

## Scenarios

Second you need to build two detailed scenarios and plans of how this plugin/skill can be used in RPA automation tasks, based on a dummy postgres/sql application in the directory, documented by schema.sql and data.sql (plan\medical_app_scenario), and a dummy financial planner API service and database in the directory (plan\financial_planner_api_scenario), using Swagger to document the API schema and the individual calls. The plan is how to build the app and fill it full of data. The scenario is how to use the plugin/skill to automate the scenario planned application, based on a clever set of rules and tasks, and then demo it to investors.

Your scenario and plan documents need to be very detailed for both Scenario 1: Medical App, and Scenario 2: Financial Planner API Service. The real difference between them is based on the language used to transpile into TypeQL; Scenario 1 is based on SQL, and Scenario 2 is based on REST API with Swagger documentation. 

In Scenario 1, the Postgres schema will be accessed via SQL  statements, and transpiled into the guardrails TypeQL schema to create the shadow database, and the SQL data imports will be transpiled into Typeql to load the data. In Scenario 2, the Postgres will be accessed via a REST API with Swagger documentation, and the guard rails agent will query the Swagger schema, which will then be transpiled into TypeDB for the schema, and the individual calls equilibrated with typeql fetch statements to create the database and load the data.

Both scenarios need to be very detailed, and include all of the details in the plan necessary for you to be able to flawlessly construct both the dummy application and the dummy API service, then setup rules, tasks, and a demo plan to demonstrate the capability to an investor.

1. First, a plan to make a detailed dummy app/api, including all of the fake data needed for the database, the simple user interface and all of the import statements. Testing must be included so the dummy app/api works correctly
2. Then a series of powerful rules that can be applied to the dummy app through the openclaw ui, to demonstrate the power of the guard rails
3. Then a plan to use the plugin/skill to automate the dummy app, including all of the steps needed to create the rules, schedule the tasks, and to review the results. Include as many functions as possible on each scenario to demonstrate the power of the guard rails.
4. Finally, a plan to demonstrate this capability to an investor, including a 1-min demo, a 5-min demo and a 20-min demo plan

Include all of the details in the plan necessary for you to be able to flawlessly construct both the dummy application and the dummy API service.

### Scenario 1: Medical App

The medical app is based on enriching the examples used in the book "Typedb for Edge AI Agents" by Volland, in this directory agent_book.

Let's model a realistic scenario: a patient receives a specific medication from a doctor or a pharmacist at a clinical site. The medication has a dosage, a frequency and contraindications, and the doctor or pharmacist has a specialty. The patient has a history of allergies, and the doctor or pharmacist needs to check the patient's history of allergies before prescribing the medication. There are many other ideas here, but you need to fill them out, and develop the raw dummy data to load into the database.

The aim is to make the scenario quite sophisticated and data rich, so you can make many interesting rules and tasks to demonstrate the power of the guard rails.

An example sketch of the sql would be 
```sql
CREATE TABLE patients (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    age INT
);

CREATE TABLE doctors (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    specialty VARCHAR(100)
);

CREATE TABLE medications (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    dosage VARCHAR(100)
);

CREATE TABLE sites (
    id INT PRIMARY KEY,
    name VARCHAR(255),
    location VARCHAR(255)
);

CREATE TABLE prescriptions (
    id INT PRIMARY KEY,
    patient_id INT FOREIGN KEY REFERENCES patients(id),
    doctor_id INT FOREIGN KEY REFERENCES doctors(id),
    medication_id INT FOREIGN KEY REFERENCES medications(id),
    site_id INT FOREIGN KEY REFERENCES sites(id),
    date_issued DATE
);

-- Query: Get all medications prescribed to patient "Alice" by which doctors at which sites
SELECT d.name, m.name, s.name, p.date_issued
FROM prescriptions p
JOIN doctors d ON p.doctor_id = d.id
JOIN medications m ON p.medication_id = m.id
JOIN sites s ON p.site_id = s.id
JOIN patients pa ON p.patient_id = pa.id
WHERE pa.name = 'Alice';
```

But you want to make to the sql more realistic, and richer so you can have great rules, and a more interesting, important scenario. Make it similar to the richness in this Medical trial example (https://github.com/Volland/typedb-for-edge-ai-agents/blob/main/manuscript/13-hypergraphs.md#complete-medical-trial-example) so patients can be proscribed drugs for which contraindications may apply, and they may have the opportunity to go on trials for new drugs, and they may have a history of allergies to certain drugs etc.

#### Medical App Implementation Plan

The medical app needs to consist of the following components:

1. A postgres/sql database with a known schema, including all of the data needed for the scenario
2. A simple, web based user interface to allow the user to view the data in the database from a localhost port compatible with OpenClaw
3. All of the import statements to load the dummy data into the database and initialise the system
4. A simple script to install and run the postgres/sql database in docker

The medical app should be constructed in a way that is easy to understand and follow, and that is easy to modify and extend (plan\medical_app_scenario\PLAN.md).

#### Medical App Rules and Tasks Scenario

Build the following (plan\medical_app_scenario\SCENARIO.md and plan\medical_app_scenario\DEMO.md):

A. A series of powerful rules that can be applied to the dummy medical app through the openclaw ui, to demonstrate the power of the guard rails
B. A plan to use the plugin/skill to automate the dummy app, including all of the steps needed for the new user to create the rules, schedule the tasks, and to review the results. Try to select rules and tasks that have real life-saving capability Include as many functions as possible on each scenario to demonstrate the power of the guard rails.
C. A plan to demonstrate this capability on the medical app to an investor, including a 1-min demo, a 5-min demo and a 20-min demo plan



### Scenario 2: Financial Planner API Service

The financial planner api service is based on a dummy financial planner api service and database in the directory (plan\financial_planner_api_scenario).

Let's model a realistic scenario: a financial planner needs to help a client to plan their financial future. The client has a name, age, income, expenses, assets, liabilities, and a financial goal. The financial planner needs to help the client to plan their financial future, based on their financial goal.

An example sketch of the sql would be 
```sql
-- Firms and licensed planners (Reg BI / firm oversight context)
CREATE TABLE firms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    crd_number VARCHAR(32) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE financial_planners (
    id SERIAL PRIMARY KEY,
    firm_id INT NOT NULL REFERENCES firms(id),
    full_name VARCHAR(255) NOT NULL,
    crd_number VARCHAR(32) UNIQUE,
    licenses VARCHAR(255), -- e.g. "7,66,CFP"
    specialty VARCHAR(100), -- retirement, small_business, estate
    email VARCHAR(255)
);

-- Households / clients
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    household_name VARCHAR(255) NOT NULL,
    primary_email VARCHAR(255),
    phone VARCHAR(50),
    date_of_birth DATE NOT NULL,
    state_of_residence CHAR(2) NOT NULL,
    filing_status VARCHAR(32), -- single, married_filing_jointly, etc.
    dependents_count INT DEFAULT 0,
    accredited_investor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- KYC, risk, and engagement with a planner
CREATE TABLE client_planner_engagements (
    id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(id),
    planner_id INT NOT NULL REFERENCES financial_planners(id),
    engagement_status VARCHAR(32) NOT NULL DEFAULT 'active', -- active, onboarding, terminated
    kyc_status VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending, verified, refresh_due
    kyc_verified_at TIMESTAMPTZ,
    risk_tolerance VARCHAR(32) NOT NULL, -- conservative, moderate, growth, aggressive
    investment_time_horizon_years INT,
    annual_income_band VARCHAR(64), -- for suitability documentation
    net_worth_band VARCHAR(64),
    last_review_date DATE,
    UNIQUE (client_id, planner_id)
);

-- Goals drive plans (retirement, education, home, emergency fund, etc.)
CREATE TABLE financial_goals (
    id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(id),
    goal_type VARCHAR(64) NOT NULL,
    description TEXT,
    target_amount NUMERIC(14,2) NOT NULL,
    target_date DATE,
    priority INT NOT NULL DEFAULT 1,
    monthly_contribution_target NUMERIC(12,2),
    status VARCHAR(32) NOT NULL DEFAULT 'active'
);

CREATE TABLE income_streams (
    id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(id),
    source_type VARCHAR(64) NOT NULL, -- w2, bonus, self_employment, rental, other
    annual_amount NUMERIC(14,2) NOT NULL,
    employer_name VARCHAR(255),
    stable_income BOOLEAN DEFAULT TRUE,
    tax_year INT NOT NULL
);

CREATE TABLE expense_categories (
    id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(id),
    category VARCHAR(64) NOT NULL,
    monthly_amount NUMERIC(12,2) NOT NULL,
    essential BOOLEAN DEFAULT TRUE
);

CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(id),
    account_type VARCHAR(64) NOT NULL, -- taxable, traditional_401k, roth_ira, hsa, cash, annuity
    institution VARCHAR(255),
    account_nickname VARCHAR(255),
    balance NUMERIC(14,2) NOT NULL,
    as_of_date DATE NOT NULL,
    liquidity_tier VARCHAR(32) -- immediate, intermediate, long_term
);

CREATE TABLE liabilities (
    id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(id),
    liability_type VARCHAR(64) NOT NULL, -- mortgage, heloc, student_loan, auto, credit_card
    outstanding_balance NUMERIC(14,2) NOT NULL,
    interest_rate_annual NUMERIC(6,4),
    minimum_payment_monthly NUMERIC(12,2),
    maturity_date DATE
);

CREATE TABLE insurance_coverages (
    id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(id),
    coverage_type VARCHAR(64) NOT NULL, -- term_life, disability, umbrella
    coverage_amount NUMERIC(14,2),
    annual_premium NUMERIC(12,2),
    beneficiary_document_current BOOLEAN DEFAULT FALSE
);

-- Recommendations and paper trail (RPA + compliance guard rails)
CREATE TABLE plan_recommendations (
    id SERIAL PRIMARY KEY,
    client_id INT NOT NULL REFERENCES clients(id),
    planner_id INT NOT NULL REFERENCES financial_planners(id),
    recommendation_type VARCHAR(64) NOT NULL, -- rebalance, contribution_change, rollover, tax_loss_harvest, product_allocation
    summary TEXT NOT NULL,
    proposed_amount NUMERIC(14,2),
    status VARCHAR(32) NOT NULL DEFAULT 'draft', -- draft, proposed, client_acknowledged, executed, cancelled
    requires_accredited_investor BOOLEAN DEFAULT FALSE,
    concentration_risk_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE suitability_reviews (
    id SERIAL PRIMARY KEY,
    recommendation_id INT NOT NULL REFERENCES plan_recommendations(id),
    review_type VARCHAR(64) NOT NULL, -- reg_bi, firm_policy, concentration, liquidity
    passed BOOLEAN NOT NULL,
    reviewer_notes TEXT,
    reviewed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Query: holistic snapshot for one household (guard-rail pre-checks: goals vs. capacity vs. risk)
SELECT
    c.household_name,
    e.risk_tolerance,
    e.kyc_status,
    COALESCE(SUM(g.target_amount), 0) AS sum_goal_targets,
    (SELECT COALESCE(SUM(annual_amount), 0) FROM income_streams i
     WHERE i.client_id = c.id AND i.tax_year = EXTRACT(YEAR FROM CURRENT_DATE)::INT) AS annual_income,
    (SELECT COALESCE(SUM(monthly_amount), 0) * 12 FROM expense_categories x WHERE x.client_id = c.id) AS annual_expenses,
    (SELECT COALESCE(SUM(balance), 0) FROM assets a WHERE a.client_id = c.id AND a.as_of_date = (
        SELECT MAX(a2.as_of_date) FROM assets a2 WHERE a2.client_id = c.id)) AS total_assets,
    (SELECT COALESCE(SUM(outstanding_balance), 0) FROM liabilities l WHERE l.client_id = c.id) AS total_liabilities
FROM clients c
JOIN client_planner_engagements e ON e.client_id = c.id
LEFT JOIN financial_goals g ON g.client_id = c.id AND g.status = 'active'
WHERE c.household_name = 'Rivera Household'
GROUP BY c.id, c.household_name, e.risk_tolerance, e.kyc_status;
```

But you want to make to the sql more realistic, and richer so you can have great rules, and a more interesting, important scenario.

#### Financial Planner API / DB Implementation Plan

The financial planner dummy service needs to consist of the following components:

1. A postgres (or equivalent) database with a known schema, including realistic firms, planners, households, goals, cash flow, balance sheet, insurance, and recommendation/suitability rows
2. A simple REST (or GraphQL) API plus a minimal web UI, an iFrame to browse clients, goals, and open recommendations from a localhost port compatible with OpenClaw, using the same approach as the medical app
3. Seed scripts / import statements to load diverse dummy households (accumulation, near-retirement, business owner, high debt, accredited vs not) so guard-rail rules have edge cases
4. Docker compose (or similar) to run database + API + UI, with automated smoke tests

The financial planner app should be constructed in a way that is easy to understand and follow, and that is easy to modify and extend (plan\financial_planner_api_scenario\PLAN.md).

#### Financial Planner Rules and Tasks Scenario

Build the following (plan\financial_planner_api_scenario\SCENARIO.md and plan\financial_planner_api_scenario\DEMO.md):

A. A series of powerful rules that can be applied to the dummy financial planner app through the openclaw ui, to demonstrate the power of the guard rails (e.g. KYC must be verified before any `executed` recommendation; risk_tolerance must align with proposed product risk; concentration and liquidity checks; accredited-investor-only products blocked unless `accredited_investor`; beneficiary flags for insurance-linked actions; debt-to-income or emergency-fund minimums before aggressive contribution changes)
B. A plan to use the plugin/skill to automate the dummy app, including all of the steps needed for the new user to create the rules, schedule the tasks, and to review the results. Include as many TypeQL-backed checks / MCP-exposed functions as possible (net worth snapshot, goal funding ratio, suitability chain, rollover eligibility, tax-advantaged account caps awareness, etc.)
C. A plan to demonstrate this capability on the financial planner scenario to an investor, including a 1-min demo, a 5-min demo and a 20-min demo plan