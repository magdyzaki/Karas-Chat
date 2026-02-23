# ارفع المشروع على GitHub
# 1. أنشئ repo جديد على github.com/new واسمه مثلاً karas-chat
# 2. عدّل الرابط أدناه بـ username واسم الـ repo
# 3. شغّل: .\push-to-github.ps1

$repoUrl = "https://github.com/YOUR_USERNAME/karas-chat.git"
# مثال: https://github.com/ahmed/karas-chat.git

Set-Location $PSScriptRoot
git remote remove origin 2>$null
git remote add origin $repoUrl
git branch -M main
git push -u origin main
