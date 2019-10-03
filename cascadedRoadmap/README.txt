This plug-in is still under development.
DO NOT USE in production.
License: will be released under Modified BSD, but currently not specified.

Install:
 1. do python setup.py bdist_egg
 2. install dist/*.egg via admin/plugin panel
 3. disable RoadmapModule in trac package
 4. enable CascadedRoadmapModule

Use:
 1. define milestones in following mannar:
   child milestone's name starts with parent's name
   ex) milestone1  (<- parent)
       milestone1.iter1 (<- child)
 2. in roadmap view, tickets are grouped by
    'starts with' rule in milestone.
