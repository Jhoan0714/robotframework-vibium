*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Interaction Fixture

*** Test Cases ***
Get Frame Missing Raises Typed Error
    [Documentation]    Validates explicit error when frame cannot be resolved.
    [Tags]    acceptance    negative
    Run Keyword And Expect Error    *could not find a frame matching*    Get Frame    missing

Fill Text Missing Value Raises Locator Error
    [Documentation]    Validates argument contract for Fill Text.
    [Tags]    acceptance    negative
    Run Keyword And Expect Error    *requires at least one locator and a value*    Fill Text    css:#name

Scroll Rejects Semantic Scoped Locator
    [Documentation]    Validates Scroll contract for scoped CSS-only selector.
    [Tags]    acceptance    negative
    Run Keyword And Expect Error    *Scroll only accepts a CSS selector*    Scroll    down    2    role:button

Find Element Missing Fails Fast With Timeout
    [Documentation]    Short find timeout fails quickly when the locator does not match.
    [Tags]    acceptance    negative
    Run Keyword And Expect Error    *element not found*    Find Element    css:#no-such-element    timeout=500ms

Click Missing Fails Fast With Timeout
    [Documentation]    Short timeout on Click fails at find when the locator does not match.
    [Tags]    acceptance    negative
    Run Keyword And Expect Error    *element not found*    Click    css:#no-such-element    timeout=500ms
