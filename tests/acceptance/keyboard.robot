*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Keyboard Fixture

*** Test Cases ***
Keyboard Type Writes Into Focused Input
    [Documentation]    Page-level type depends on focus.
    [Tags]    acceptance    keyboard
    Click    css:#name
    Keyboard Type    Ada
    ${value}=    Get Value    css:#name
    Should Be Equal    ${value}    Ada

Keyboard Key Press Sends Enter
    [Documentation]    Page-level press of Enter after focusing the field.
    [Tags]    acceptance    keyboard
    Click    css:#q
    Keyboard Key    press    Enter
    ${out}=    Get Text    css:#out
    Should Be Equal    ${out}    enter

Press Keys Targets Element
    [Documentation]    Element press with required locator.
    [Tags]    acceptance    keyboard    interaction
    Press Keys    Enter    css:#q
    ${out}=    Get Text    css:#out
    Should Be Equal    ${out}    enter

Keyboard Key Down And Up Execute
    [Documentation]    Hold/release a modifier without error.
    [Tags]    acceptance    keyboard
    Keyboard Key    down    Shift
    Keyboard Key    up    Shift
