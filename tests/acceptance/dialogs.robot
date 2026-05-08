*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser
Test Setup    Go To Blank Page

*** Test Cases ***
Dialog Accept Handles Alert
    [Documentation]    Validates accept handler for alert dialog.
    [Tags]    acceptance    dialogs
    Dialog Accept
    Trigger Alert Dialog

Dialog Dismiss Handles Confirm
    [Documentation]    Validates dismiss handler for confirm dialog.
    [Tags]    acceptance    dialogs
    Dialog Dismiss
    Trigger Confirm Dialog
