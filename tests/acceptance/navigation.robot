*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser

*** Test Cases ***
Navigate To Base Url
    [Documentation]    Validates Go To and Get Url with a real page.
    [Tags]    acceptance    navigation    core
    Go To    ${BASE_URL}
    ${url}=    Get Url
    Should Contain    ${url}    example.com

History Back And Forward
    [Documentation]    Validates Go Back and Go Forward without errors.
    [Tags]    acceptance    navigation
    Go To    ${BASE_URL}
    Go To Blank Page
    Go Back
    ${back_url}=    Get Url
    Should Contain    ${back_url}    example.com
    Go Forward
    ${forward_url}=    Get Url
    Should Be Equal    ${forward_url}    about:blank

Reload Keeps Location
    [Documentation]    Validates Reload on the active tab.
    [Tags]    acceptance    navigation    core
    Go To    ${BASE_URL}
    ${before}=    Get Url
    Reload
    ${after}=    Get Url
    Should Contain    ${after}    example.com

New Page Switch Page And List Pages
    [Documentation]    Validates second tab, listing, switching focus, and closing a tab.
    [Tags]    acceptance    navigation    core
    Go To    ${BASE_URL}
    ${first}=    Get Active Page
    New Page    about:blank
    ${second}=    Get Active Page
    ${urls}=    List Pages
    ${n}=    Get Length    ${urls}
    Should Be Equal As Integers    ${n}    2
    Switch Page    ${first}
    ${u1}=    Get Url
    Should Contain    ${u1}    example.com
    Switch Page    ${second}
    Close Page    scope=${second}
    ${u2}=    Get Url
    Should Contain    ${u2}    example.com
