*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser

*** Test Cases ***
Library Loads
    [Documentation]    Ensures the library opens and basic navigation works.
    [Tags]    smoke    core
    Go To Blank Page
    ${url}=    Get Url
    Should Be Equal    ${url}    about:blank
