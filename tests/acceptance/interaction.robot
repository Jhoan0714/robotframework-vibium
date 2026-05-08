*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Interaction Fixture

*** Test Cases ***
Fill Element Updates Input Value
    [Documentation]    Validates Fill Element and Get Element Value.
    [Tags]    acceptance    interaction    core
    Fill Element    css:#name    Ada Lovelace
    ${value}=    Get Element Value    css:#name
    Should Be Equal    ${value}    Ada Lovelace

Click Element Updates Fixture State
    [Documentation]    Validates Click Element and Get Element Attr.
    [Tags]    acceptance    interaction
    Click Element    css:#save
    ${clicked}=    Get Element Attr    data-clicked    css:#save
    Should Be Equal    ${clicked}    1
