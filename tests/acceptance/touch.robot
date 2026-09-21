*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Mouse Fixture

*** Test Cases ***
Touch Tap Executes
    [Documentation]    Validates page-level Touch Tap at viewport coordinates.
    [Tags]    acceptance    touch
    Touch Tap    20    20
