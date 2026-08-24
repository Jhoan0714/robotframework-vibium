*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser

*** Test Cases ***
Set Page Content Replaces Document
    [Documentation]    Injects HTML in place; locators see the new DOM.
    [Tags]    acceptance    document
    Go To Blank Page
    Set Page Content    <html><body><h1 id="t">hello-content</h1></body></html>
    ${text}=    Get Text    css:#t
    Should Be Equal    ${text}    hello-content
    ${url}=    Get Url
    Should Contain    ${url}    about:blank
