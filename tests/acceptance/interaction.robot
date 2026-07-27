*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Interaction Fixture

*** Test Cases ***
Fill Text Updates Input Value
    [Documentation]    Validates Fill Text and Get Value.
    [Tags]    acceptance    interaction    core
    Fill Text    css:#name    Ada Lovelace
    ${value}=    Get Value    css:#name
    Should Be Equal    ${value}    Ada Lovelace

Click Updates Fixture State
    [Documentation]    Validates Click and Get Attribute.
    [Tags]    acceptance    interaction
    Click    css:#save
    ${clicked}=    Get Attribute    data-clicked    css:#save
    Should Be Equal    ${clicked}    1
