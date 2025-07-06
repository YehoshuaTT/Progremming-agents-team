# Files to Delete - Detailed List
## **Outdated and No Longer Relevant Files**

### **📁 /docs/ - Old Reports**
```
DAILY_ACHIEVEMENT_REPORT_2025-07-04.md
DAILY_ACHIEVEMENT_REPORT_2025-07-04_EVENING.md
DAILY_ACHIEVEMENT_REPORT_2025-07-04_FINAL.md
PROGRESS_REPORT_20250706.md
PROGRESS_REPORT_CURRENT.md
WORK_PLAN_CURRENT.md
CONCLUSIONS_CURRENT.md
```

### **📁 /project_management/ - Old Plans**
```
tracking/daily_reports/ (entire directory)
planning/legacy_plans/ (if exists)
reports/outdated/ (if exists)
```

### **📁 /reports/ - Outdated Reports**
```
benchmark_report_*.md (old reports)
daily_progress_*.md (old daily reports)
```

### **📁 /development/ - Old Development Files**
```
cache/demo_experience_database.db (if not needed)
debug/old_debug_files/ (if exists)
```

### **📁 /archive/ - Entire Directory**
```
archive/backups/
archive/legacy/
archive/old-versions/
```

---

## **Important Files to Update**

### **🔄 Immediate Update Required**
- `FINAL_DEVELOPMENT_SUMMARY.md` → July 2025 status
- `FINAL_EVALUATION_REPORT.md` → Current test results
- `PROMPT_OPTIMIZATION_PLAN.md` → Immediate implementation
- `README.md` → Add information about known issues

### **📝 General Update**
- `SYSTEM_OVERVIEW.md` → Add new components
- `QUICK_REFERENCE.md` → Update commands and workflows
- `DEPENDENCIES.md` → Update requirements

---

## **Recommended Actions**

### **Step 1: Backup**
```powershell
# Create backup before deletion
New-Item -ItemType Directory -Path "backup_before_cleanup"
Copy-Item "docs/DAILY_ACHIEVEMENT_REPORT_*" "backup_before_cleanup/" -Recurse
Copy-Item "project_management/tracking/daily_reports/" "backup_before_cleanup/" -Recurse
```

### **Step 2: Deletion**
```powershell
# Delete outdated files
Remove-Item "docs/DAILY_ACHIEVEMENT_REPORT_2025-07-04*.md"
Remove-Item "docs/PROGRESS_REPORT_*.md"
Remove-Item "docs/WORK_PLAN_CURRENT.md"
Remove-Item "docs/CONCLUSIONS_CURRENT.md"
Remove-Item "archive/" -Recurse -Force
```

### **Step 3: Reorganization**
```powershell
# Create new directories
New-Item -ItemType Directory -Path "docs/current/"
New-Item -ItemType Directory -Path "docs/archive/"
Move-Item "docs/COMPREHENSIVE_PROJECT_REVIEW_EN.md" "docs/current/"
```

---

**📅 This list was created in July 2025 for project organization**
