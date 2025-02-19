import json
import logging
import os
import sys
import yaml

from typer.testing import CliRunner

from datacontract.cli import app
from datacontract.export.dbt_converter import to_dbt
from datacontract.model.data_contract_specification import \
    DataContractSpecification

logging.basicConfig(level=logging.DEBUG, force=True)


def test_cli():
    runner = CliRunner()
    result = runner.invoke(app, [
        "export",
        "./examples/local-json/datacontract.yaml",
        "--format", "dbt"
    ])
    assert result.exit_code == 0


def test_to_dbt():
    data_contract = DataContractSpecification.from_string(read_file("./examples/export/datacontract.yaml"))
    expected_dbt_model = """
version: 2
models:
  - name: orders    
    config:
      materialized: table
      contract:
        enforced: true
    description: The orders model
    columns:
      - name: order_id
        data_type: VARCHAR
        constraints:
          - type: not_null
          - type: unique
        tests:
          - dbt_expectations.expect_column_value_lengths_to_be_between:
              min_value: 8
              max_value: 10
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: ^B[0-9]+$      
        meta:
          classification: sensitive
          pii: true
        tags:
          - order_id
      - name: order_total
        data_type: NUMBER
        constraints:
          - type: not_null    
        description: The order_total field
        tests:
          - dbt_expectations.expect_column_values_to_be_between:
               min_value: 0
               max_value: 1000000
      - name: order_status
        data_type: TEXT
        constraints:
          - type: not_null
        tests:
          - accepted_values:
              values:
                - 'pending'
                - 'shipped'
                - 'delivered'
"""

    result = yaml.safe_load(to_dbt(data_contract))

    assert result == yaml.safe_load(expected_dbt_model)


def read_file(file):
    if not os.path.exists(file):
        print(f"The file '{file}' does not exist.")
        sys.exit(1)
    with open(file, 'r') as file:
        file_content = file.read()
    return file_content
