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

Nested Find Element Scope
    [Documentation]    Find Element returns a handle usable as scope for nested find.
    [Tags]    acceptance    interaction    core
    Reset Nested Find Fixture
    ${card}=    Find Element    css:#card
    ${desc}=    Describe Element    ${card}
    Should Contain    ${desc}    div
    Click    css:button    scope=${card}
    ${clicked}=    Get Attribute    data-clicked    css:#inner-btn
    Should Be Equal    ${clicked}    1
    ${btn}=    Find Element    css:button    scope=${card}
    ${btn_desc}=    Describe Element    ${btn}
    Should Contain    ${btn_desc}    button
    @{items}=    Find Elements    css:li    scope=${card}
    ${n}=    Get Length    ${items}
    Should Be Equal As Integers    ${n}    ${2}
    ${count}=    Count Elements    css:li    scope=${card}
    Should Be Equal As Integers    ${count}    ${2}
