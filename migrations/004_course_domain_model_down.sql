-- Gayatri AI Central Platform — Down Migration 004: Course Domain Model (Phase 02)

DROP TABLE IF EXISTS organization_course_offerings;
DROP TABLE IF EXISTS course_versions;

ALTER TABLE courses DROP COLUMN visibility;
ALTER TABLE sessions DROP COLUMN course_version_id;
ALTER TABLE sessions DROP COLUMN class_id;
ALTER TABLE enrollments DROP COLUMN course_offering_id;
ALTER TABLE enrollments DROP COLUMN class_id;
