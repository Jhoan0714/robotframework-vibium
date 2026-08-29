*** Settings ***
Resource    resources/common.resource

Suite Teardown    Close All Browsers

*** Variables ***
${VIBIUM_CONNECT_URL}    ${EMPTY}

*** Test Cases ***
Open Browser Remote Connect When Configured
    [Documentation]
    ...    ``Open Browser    url=...`` against a reachable BiDi WebSocket endpoint.
    ...    Skips when ``VIBIUM_CONNECT_URL`` is empty. Pass the URL with
    ...    ``-v VIBIUM_CONNECT_URL:ws(s)://...`` or export the env var before ``robot``.
    [Tags]    acceptance    no-ci
    Pass Execution If    '${VIBIUM_CONNECT_URL}' == ''    No VIBIUM_CONNECT_URL configured
    ${browser}=    Open Browser    url=${VIBIUM_CONNECT_URL}
    Go To Blank Page
    ${url}=    Get Url
    Should Be Equal    ${url}    about:blank
    Close Browser    browser=${browser}
