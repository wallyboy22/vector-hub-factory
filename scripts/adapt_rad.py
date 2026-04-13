import re

with open('ui/apps/rad/index.html.backup', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("APP_ID = 'raf'", "APP_ID = 'rad'")
content = content.replace('src="${API_URL}/pdf/raf', 'src="${API_URL}/pdf/rad')
content = content.replace('/pdf/raf#page=', '/pdf/rad#page=')
content = content.replace("report: 'raf'", "report: 'rad'")
content = content.replace("reports['raf']", "reports['rad']")
content = content.replace('#E8503A', '#812411')
content = content.replace('primary-color: #E8503A', 'primary-color: #812411')

with open('ui/apps/rad/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - RAD adapted from RAF')