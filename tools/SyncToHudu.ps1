<#
.SYNOPSIS
    Syncs agents from Tactical RMM to Hudu.

.REQUIREMENTS
    - You will need an API key from Hudu and Tactical RMM which should be passed as parameters (DO NOT hard code in script).  
    - This script imports/installs powershell module https://github.com/lwhitelock/HuduAPI which you may have to manually install if errors.

.NOTES
    - Ideally, this script should be run on the Tactical RMM server however since there is no linux agent, 
      you'll have to run this on one of your trusted Windows devices with PowerShell 7 installed.
    - This script compares Tactical's Client Name with Hudu's Company Names and if there is a match (case sensitive) 
      it creates/syncs asset based on hostname. Nothing will be created or synced if a company match is not found.  

.PARAMETERS
    - $ApiKeyTactical   - Tactical API Key
    - $ApiUrlTactical   - Tactical API Url
    - $ApiKeyHudu       - Hudu API Key
    - $ApiUrlHudu       - Hudu API Url
    - $HuduAssetName    - The name of the asset in Hudu. Defaults to "TacticalRMM Agents"
    - $CopyMode         - If set, the script will not delete the assets in Hudu before syncing (Any items deleted from Tactical will remain in Hudu until manually removed).  
.EXAMPLE
    - Tactical_Hudu_Sync.ps1 -ApiKeyTactical 1234567 -ApiUrlTactical api.yourdomain.com -ApiKeyHudu 1248ABBCD3 -ApiUrlHudu hudu.yourdomain.com -HuduAssetName "Tactical Agents" -CopyMode
.TODO
    - fix Get-ArrayData so that it doesn't display all in one line
    - add optional Hudu Relations to the built in Office 365 integration (e.g. last_logged_in_user so you can match a logged in user with their respective workstations)
    - add more tactical fields
    - reduce the amount of rest calls made
		
.VERSION
    - v1.2 Updated fields and list view as per new requirements
#>

#Requires -Version 7.0

param(
    [string] $ApiKeyTactical,
    [string] $ApiUrlTactical,
    [string] $ApiKeyHudu,
    [string] $ApiUrlHudu,
    [string] $HuduAssetName,
    [switch] $CopyMode
)

function Get-ArrayData {
    param(
        $data
    )
    $formattedData = $data -join ", "
    return $formattedData
}

function Get-CustomFieldData {
    param(
        $label,
        $arrayData
    )
    $value = ($arrayData | Where-Object { $_.label -eq $label }).value
    return $value
}

if ([string]::IsNullOrEmpty($ApiKeyTactical)) {
    throw "ApiKeyTactical must be defined. Use -ApiKeyTactical <value> to pass it."
}

if ([string]::IsNullOrEmpty($ApiUrlTactical)) {
    throw "ApiUrlTactical without the https:// must be defined. Use -ApiUrlTactical <value> to pass it."
}

if ([string]::IsNullOrEmpty($ApiKeyHudu)) {
    throw "ApiKeyHudu must be defined. Use -ApiKeyHudu <value> to pass it."
}

if ([string]::IsNullOrEmpty($ApiUrlHudu)) {
    throw "ApiUrlHudu without the https:// must be defined. Use -ApiUrlHudu <value> to pass it."
}

if ([string]::IsNullOrEmpty($HuduAssetName)) {
    Write-Output "HuduAssetName param not defined. Using default name TacticalRMM Agents."
    $HuduAssetName = "TacticalRMM Agents v6"
}

try {
    if (Get-Module -ListAvailable -Name HuduAPI) {
        Import-Module HuduAPI 
    } else {
        Install-Module HuduAPI -Force
        Import-Module HuduAPI
    }
}
catch {
    throw "Installation of HuduAPI failed. Please install HuduAPI manually first by running: 'Install-Module HuduAPI' on server."
}

$headers = @{
    'X-API-KEY' = $ApiKeyTactical
}

New-HuduAPIKey $ApiKeyHudu 
New-HuduBaseURL "https://$ApiUrlHudu" 

$huduAssetLayout = Get-HuduAssetLayouts -name $HuduAssetName

# Create Hudu Asset Layout if it does not exist
if (!$huduAssetLayout){
    $fields = @(
    @{
        label = 'AV'
        field_type = 'CheckBox'
        hint = 'Antivirus Status'
        position = 1
        show_in_list = $true
    },
    @{
        label = 'Backup'
        field_type = 'CheckBox'
        hint = 'Backup Status'
        position = 2
        show_in_list = $true
    },
    @{
        label = 'Update'
        field_type = 'CheckBox'
        hint = 'Patch Status'
        position = 3
        show_in_list = $true
    },
    @{
        label = 'Reboot'
        field_type = 'CheckBox'
        hint = 'Reboot Status'
        position = 4
        show_in_list = $true
    },
    @{
        label = 'Username'
        field_type = 'Text'
        position = 5
        show_in_list = $true
    },
    @{
        label = 'Site'
        field_type = 'Text'
        position = 6
        show_in_list = $true
    },
    @{
        label = 'AV Details'
        field_type = 'RichText'
        position = 7
    },
    @{
        label = 'Backup Details'
        field_type = 'RichText'
        position = 8
    },
    @{
        label = 'Client Name'
        field_type = 'Text'
        position = 9
    },
    @{
        label = 'Computer Name'
        field_type = 'Text'
        position = 10
    },
    @{
        label = 'Status'
        field_type = 'CheckBox'
        hint = 'Online/Offline'
        position = 11
    },
    @{
        label = 'Description'
        field_type = 'Text'
        position = 12
    },
    @{
        label = 'Last Seen'
        field_type = 'Text'
        position = 13
    },
    @{
        label = 'Overdue Dashboard Alert'
        field_type = 'CheckBox'
        hint = ''
        position = 14
    },
    @{
        label = 'Overdue Email Alert'
        field_type = 'CheckBox'
        hint = ''
        position = 15
    },
    @{
        label = 'Overdue Text Alert'
        field_type = 'CheckBox'
        hint = ''
        position = 16
    },
    @{
        label = 'Pending Actions Count'
        field_type = 'Number'
        hint = ''
        position = 17
    },
    @{
        label = 'Make Model'
        field_type = 'Text'
        position = 18
    },
    @{
        label = 'CPU Model'
        field_type = 'RichText'
        position = 19
    },
    @{
        label = 'Total RAM'
        field_type = 'Number'
        hint = ''
        position = 20
    },
    @{
        label = 'Operating System'
        field_type = 'Text'
        position = 21
    },
    @{
        label = 'Local Ips'
        field_type = 'Text'
        position = 22
    },
    @{
        label = 'Public Ip'
        field_type = 'Text'
        position = 23
    },
    @{
        label = 'Graphics'
        field_type = 'Text'
        position = 24
    },
    @{
        label = 'Disks'
        field_type = 'RichText'
        position = 25
    },    
    @{
        label = 'Created Time'
        field_type = 'Text'
        position = 26
    },
    @{
        label = 'Agent Id'
        field_type = 'Text'
        position = 27
    })
    New-HuduAssetLayout -name $HuduAssetName -icon "fas fa-fire" -color "#5B17F2" -icon_color "#ffffff" -include_passwords $false -include_photos $false -include_comments $false -include_files $false -fields $fields
    Start-Sleep -Seconds 5
    $huduAssetLayout = Get-HuduAssetLayouts -name $HuduAssetName
}

# If not CopyMode set, delete all assets before performing sync
if (!$CopyMode){
    $assetsToDelete = Get-HuduAssets -assetlayoutid $huduAssetLayout.id
    foreach ($asset in $assetsToDelete){
        $assetId        = $asset.id
        $assetName      = $asset.name
        $assetCompanyId = $asset.company_id
        Write-Host "Deleting $assetName from company id $assetCompanyId with an asset id of $assetId"
        Remove-HuduAsset -Id $asset.id -CompanyId $asset.company_id -Confirm:$false
    }
}

try {
    $agentsResult = Invoke-RestMethod -Method 'Get' -Uri "https://$ApiUrlTactical/agents" -Headers $headers -ContentType "application/json"
}
catch {
    throw "Error invoking rest call on Tactical RMM with error: $($PSItem.ToString())"
}

foreach ($agents in $agentsResult) {

    $agentId = $agents.agent_id

    try {
        $agentDetailsResult = Invoke-RestMethod -Method 'Get' -Uri "https://$ApiUrlTactical/agents/$agentId" -Headers $headers -ContentType "application/json"

        # Get agent checks
        $checksResult = Invoke-RestMethod -Method 'Get' -Uri "https://$ApiUrlTactical/agents/$agentId/checks/" -Headers $headers -ContentType "application/json"
        
        # Initialize variables for Antivirus and Bitdefender
        $avStatus = $false
        $avDetails = "Unknown"
        $backupStatus = $false
        $backupDetails = "Unknown"

        foreach ($check in $checksResult) {
            if ($check.readable_desc -like "*GI - GetAcronisStatus.py*") {
                if ($check.check_result.status -eq "passing") {
                    $backupStatus = $true
                    $backupDetails = "OK: " + $check.check_result.stdout
                } else {
                    $backupDetails = "Error: " + $check.check_result.stdout
                }
            }
            elseif ($check.readable_desc -like "*GI - GetBidefenderStatus.py*") {
                if ($check.check_result.status -eq "passing") {
                    $avStatus = $true
                    $avDetails = "OK: " + $check.check_result.stdout
                } else {
                    $avDetails = "Error: " + $check.check_result.stdout
                }
            }
        }
    }
    catch {
        Write-Error "Error invoking agent detail or checks rest call on Tactical RMM with error: $($PSItem.ToString())"
    }

    $textDisk   = Get-ArrayData -data $agentDetailsResult.disks
    $textCpu    = Get-ArrayData -data $agentDetailsResult.cpu_model

    $fieldData = @(
	@{
        av                      = $avStatus
        backup                  = $backupStatus
        update                  = !$agents.has_patches_pending
        reboot                  = !$agents.needs_reboot
        username                = $agentDetailsResult.last_logged_in_user
        site                    = $agents.site_name
        av_details              = $avDetails
        backup_details          = $backupDetails
        client_name             = $agents.client_name
        computer_name           = $agents.hostname
        status                  = $agents.status
        description             = $agents.description
        last_seen               = $agents.last_seen
        overdue_dashboard_alert = $agents.overdue_dashboard_alert
        overdue_email_alert     = $agents.overdue_email_alert
        overdue_text_alert      = $agents.overdue_text_alert
        pending_actions_count   = $agents.pending_actions_count
        total_ram               = $agentDetailsResult.total_ram
        local_ips               = $agentDetailsResult.local_ips
        created_time            = $agentDetailsResult.created_time
        graphics                = $agentDetailsResult.graphics
        make_model              = $agentDetailsResult.make_model
        operating_system        = $agentDetailsResult.operating_system
        public_ip               = $agentDetailsResult.public_ip
        disks                   = $textDisk
        cpu_model               = $textCpu
        agent_id                = $agentId
	})

    $huduCompaniesFiltered = Get-HuduCompanies -name $agents.client_name

    # If Hudu Company matches a Tactical Client
    if ($huduCompaniesFiltered){
        
        $asset = Get-HuduAssets -name $agents.hostname -assetlayoutid $huduAssetLayout.id -companyid $huduCompaniesFiltered.id

        $huduAgentId = Get-CustomFieldData -label "Agent Id" -arrayData $asset.fields

        # If asset exist and the Hudu asset matches Tactical based on agent_id update. Else create new asset
        if ($asset -and $huduAgentId -eq $agentId){
            Set-HuduAsset -name $agents.hostname -company_id $huduCompaniesFiltered.id -asset_layout_id $huduAssetLayout.id -fields $fieldData -asset_id $asset.id
        } else {
            Write-Host "Asset does not exist in Hudu. Creating $($agents.hostname)"
            New-HuduAsset -name $agents.hostname -company_id $huduCompaniesFiltered.id -asset_layout_id $huduAssetLayout.id -fields $fieldData
        }
    }
}