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

Click And Get Text With Element Handle
    [Documentation]    Action/getter keywords accept a Find Element handle as the sole target.
    [Tags]    acceptance    interaction    core
    Reset Nested Find Fixture
    ${card}=    Find Element    css:#card
    ${btn}=    Find Element    css:button    scope=${card}
    ${label}=    Get Text    ${btn}
    Should Be Equal    ${label}    Go
    Click    ${btn}
    ${clicked}=    Get Attribute    data-clicked    ${btn}
    Should Be Equal    ${clicked}    1
    Double Click    ${btn}
    ${clicked2}=    Get Attribute    data-clicked    css:#inner-btn
    Should Be Equal    ${clicked2}    3

Hover With Element Handle
    [Documentation]    Hover accepts a Find Element handle as the sole target.
    [Tags]    acceptance    interaction
    Reset Hover Fixture
    ${el}=    Find Element    css:#hover-target
    Hover    ${el}
    ${hovered}=    Get Attribute    data-hovered    ${el}
    Should Be Equal    ${hovered}    1

Fill Text With Element Handle
    [Documentation]    Fill Text accepts a Find Element handle with explicit value=.
    [Tags]    acceptance    interaction
    ${input}=    Find Element    css:#name
    Fill Text    ${input}    value=Grace Hopper
    ${value}=    Get Value    ${input}
    Should Be Equal    ${value}    Grace Hopper
