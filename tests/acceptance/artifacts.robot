*** Settings ***
Resource    resources/common.resource
Suite Setup    Open Test Browser
Suite Teardown    Close Test Browser

*** Test Cases ***
Take Screenshot Writes Artifact
    [Documentation]    Validates screenshot artifact generation.
    [Tags]    acceptance    artifacts
    Go To    ${BASE_URL}
    ${path}=    Take Screenshot    output_path=acceptance/screenshot.png    embed=${FALSE}
    Should Not Be Empty    ${path}
    File Should Exist    ${path}

Save Pdf Writes Artifact
    [Documentation]    Validates PDF artifact generation.
    [Tags]    acceptance    artifacts
    Go To    ${BASE_URL}
    ${path}=    Save Pdf    output_path=acceptance/report.pdf    embed=${FALSE}
    Should Not Be Empty    ${path}
    File Should Exist    ${path}

Take Element Screenshot Writes Artifact
    [Documentation]    Validates element screenshot path on a stable fixture-sized page.
    [Tags]    acceptance    artifacts    core
    Go To    data:text/html,<main><div id='box' style='width:80px;height:40px;background:rgb(51,102,153)'>inside</div></main>
    ${path}=    Take Element Screenshot    css:#box    output_path=acceptance/element-box.png    embed=${FALSE}
    Should Not Be Empty    ${path}
    File Should Exist    ${path}
