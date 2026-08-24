*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Reset Mouse Fixture

*** Test Cases ***
Mouse Move And Click Execute
    [Documentation]    Validates mouse move and click commands execute without error.
    [Tags]    acceptance    mouse
    Mouse Move    20    20
    Mouse Click    20    20

Mouse Down And Up Execute
    [Documentation]    Validates mouse button press/release commands.
    [Tags]    acceptance    mouse
    Mouse Move    10    10
    Mouse Down
    Mouse Up

Mouse Wheel Executes
    [Documentation]    Validates mouse wheel command executes without error.
    [Tags]    acceptance    mouse
    Mouse Wheel    0    120
