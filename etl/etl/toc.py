# All the different kinds of TOCs that we have on our system
#
# At this time the templates come from the python here, because
# they are actually generated.  There's an opportunity to have a
# template that generates jinja templates, but it's probably easier
# to just have them here.


import csv
import sys


class Toc:
    def __init__(self):
        self.proposals = None

        # Defaults to the simple list for groups of proposals
        self.proposal_formatter = WikiListTocProposalFormatter()

    def process_competition(self, competition):
        """Processes a COMPETITION after it has been built.  This
        is separate from the initializer because we want to
        declare the TOCs somewhere ahead of all the competition
        processing.

        It should use the self.proposals attribute to process the data,
        which will be set to all the proposals of the competition
        in the case that it wasn't set from outside."""
        pass

    def template_file(self):
        """Returns a jinja template file, usually generated in place
        that will be uploaded along with the json file generated
        by the dictionary returned by grouped_data"""
        return ""

    def grouped_data(self):
        """Returns a dictionary that should be uploaded alongside
        the template to be handled by torque with rendering the Toc"""
        return {}


class TocProposalFormatter:
    """Base class for formatters for how TOC lists are built.  For instance,
    in grouped TOCs, this formatter will be applied to each section that has
    a list of proposals."""

    def prefix(self, group_var_name):
        """The PREFIX of the section containing a list of proposals.  To be
        added out before each list is done.  GROUP_VAR_NAME names the
        what the group will be called in the template.  It's icnluded in the
        prefix in case the prefix needs to collect general information about
        the group."""
        return ""

    def format_proposal(self, group_var_name, id_var_name):
        """The formatting line for a proposal.  Because the proposals are handed
        to the TOC at run time of the torque server, not of a etl pipeline, two
        pieces of information are needed.  The first is the GROUP_VAR_NAME, naming
        what the group is called in the template (usually the competition name).
        The second is the ID_VAR_NAME which holds the variable name of the id
        for the given proposal.  Usually this is proposal_id for most templates
        created in this file, but it can be different.  Between these, the template,
        and therefore the formatted, can get at the proposal information."""
        return ""

    def suffix(self):
        """The SUFFIX of the section containing a list of proposals.  To be
        added out after each list is done."""
        return ""


class WikiListTocProposalFormatter(TocProposalFormatter):
    """A TocProposalFormatter for simple wiki lists, meaning a new line separated
    list of values that start with '*'.  These proposals are then rendered
    according to the torque configured TOC template (via the 'toc_lines' variable)."""

    def format_proposal(self, group_var_name, id_var_name):
        return "* {{ toc_lines[%s] }}\n" % id_var_name


class WikiTableTocProposalFormatter(TocProposalFormatter):
    """A TocProposalFormatter for wiki tables.  The columns and column_headings
    must be passed in at the beginning, to build a list, and it's assumed that
    people viewing these proposals will have access to those columns, as no
    conditional check on permissions is made.

    The wiki tables themselves are sortable and styled."""

    def __init__(self, column_definitions):
        """Initializes with COLUMN_DEFINITIONS, which is an array of
        the following dictionaries:

        {
            name: String (required if processor omitted),
            processor: Function (required if name omitted),
            heading: String (required),
            link: Boolean (defaults to false),
            right_aligned: Boolean (defaults to false)
        }

        Where NAME is the name of the column in the proposals,
        PROCESSOR is a function taking a the group_var and id_var as arguments
        (as those are necessary to find the information at template render
        time) and returning a String, HEADING is the heading for that column in
        the table, LINK notes that this column should link against the proposal
        pages, and RIGHT_ALIGNED is whether the data in this column should be
        right aligned.

        For NAME vs PROCESSOR, only one can be present, because either
        the column is looked up directly, or the proposal is sent to
        the PROCESSOR.  If both are included, NAME will be used.
        """
        self.column_definitions = column_definitions

    def prefix(self, group_var_name):
        template = '{| class="wikitable bs-exportable exportable sortable" style="border-style: solid; border-color: gray; border-width: 5px;"\n'
        for column_def in self.column_definitions:
            # This conditional is whether the viewer has permissions to this column, which
            # we ascertain by looking at the first proposal in the list
            if "name" in column_def:
                template += (
                    "{%% if %s|length == 0 or '%s' in (%s.values()|list|first) -%%}\n"
                    % (
                        group_var_name,
                        column_def["name"],
                        group_var_name,
                    )
                )
            template += "! %s\n" % column_def["heading"]

            if "name" in column_def:
                template += "{% endif -%}\n"
        return template

    def format_proposal(self, group_var_name, id_var_name):
        from etl import competition

        template = "|-\n"
        for column_def in self.column_definitions:
            heading = column_def["heading"]
            link = column_def.get("link", False)
            right_aligned = column_def.get("right_aligned", False)

            if "name" in column_def:
                template += "{%% if '%s' in %s[%s] -%%}\n" % (
                    column_def["name"],
                    group_var_name,
                    id_var_name,
                )
            template += "| "

            template += " style='vertical-align:top;"
            if right_aligned:
                template += "text-align:right;"
            template += "' |"

            if link:
                template += "[[{{ %s[%s]['%s'] }}|" % (
                    group_var_name,
                    id_var_name,
                    competition.MediaWikiTitleAdder.title_column_name,
                )

            if "name" in column_def:
                template += "{{ %s[%s]['%s'] }}" % (
                    group_var_name,
                    id_var_name,
                    column_def["name"],
                )
            elif "processor" in column_def:
                template += column_def["processor"](group_var_name, id_var_name)
            else:
                raise Exception(
                    "Neither name nor processor was present in column definition for {}".format(
                        heading
                    )
                )

            if link:
                template += "]]"

            template += "\n"
            if "name" in column_def:
                template += "{% endif -%}\n"

        return template

    def suffix(self):
        return "|}\n"


class GenericToc(Toc):
    """A Toc that prints a grouped set of proposals with each group
    being a heading in the eventual wiki page."""

    def __init__(self, name, column, initial_groupings=None, sort=None):
        """Set up the Toc by giving a NAME for the Toc and a COLUMN which
        it's based on.

        INITIAL_GROUPINGS is an optional Array of different specified groupings,
        which gives it an order as groups (the value of the specified COLUMN for
        various proposals) get added to the end when not found.

        If INITIAL_GROUPINGS is missing, then the groups are sorted alphabetically,
        unless SORT is passed, which overrides that determiniation (either for
        sorting or against)."""

        super().__init__()
        self.name = name
        self.column = column
        self.groupings = initial_groupings if initial_groupings is not None else []
        if sort is not None:
            self.sort = sort
        else:
            self.sort = initial_groupings is None
        self.data = {x: [] for x in self.groupings}

    def process_competition(self, competition):
        self.competition_name = competition.name

        if self.proposals is None:
            self.proposals = competition.ordered_proposals()

        for proposal in self.proposals:
            grouping = proposal.cell(self.column)
            if grouping not in self.data:
                self.groupings.append(grouping)
                self.data[grouping] = []
            self.data[grouping].append(proposal.key())

        if self.sort:
            self.data = {
                grouping: self.data[grouping] for grouping in sorted(self.groupings)
            }

    def template_file(self):
        template = "__TOC__"
        template += ""
        template += "{% for group_name, proposal_ids in groups.items() %}\n"
        template += "    {%- set proposals_in_group = [] %}\n"
        template += "    {%- for proposal_id in proposal_ids %}\n"
        template += (
            "        {%%- if proposal_id in %s.keys() %%}\n" % self.competition_name
        )
        template += '            {{- "" if proposals_in_group.append(proposal_id) }}\n'
        template += "        {%- endif %}\n"
        template += "    {%- endfor %}\n"
        template += "    {%- if proposals_in_group|length > 0 %}\n"

        # This line is so that we can have counts and still link into it
        template += "<div id='{{ group_name }}'></div>\n"
        template += "= {{ group_name }} ({{ proposals_in_group|length }}) =\n"
        template += self.proposal_formatter.prefix(self.competition_name)
        template += "        {%- for proposal_id in proposals_in_group %}\n"
        template += self.proposal_formatter.format_proposal(
            self.competition_name, "proposal_id"
        )
        template += "        {%- endfor %}\n"
        template += self.proposal_formatter.suffix()
        template += "    {%- endif %}\n"
        template += "{%- endfor %}\n"
        return template

    def grouped_data(self):
        return {"groups": self.data}


class GenericMultiLineToc(GenericToc):
    """A special case of GenericToc for columns that have multiple
    values in them (like a list of keywords), so that proposals
    can show up multiple times on the Toc"""

    def process_competition(self, competition):
        self.competition_name = competition.name

        # Allows someone outside to set which specific proposals we should use.
        if self.proposals is None:
            self.proposals = competition.ordered_proposals()

        for proposal in self.proposals:
            groupings = proposal.cell(self.column).split("\n")
            for grouping in groupings:
                if grouping not in self.data:
                    self.groupings.append(grouping)
                    self.data[grouping] = []
                self.data[grouping].append(proposal.key())

        if self.sort:
            self.data = {
                grouping: self.data[grouping] for grouping in sorted(self.groupings)
            }


class ListToc(Toc):
    """A Toc that just lists all the proposals someone has access to."""

    def __init__(self, name):
        super().__init__()
        self.name = name

    def process_competition(self, competition):
        self.competition_name = competition.name

        if self.proposals is None:
            self.proposals = competition.ordered_proposals()

        self.keys = [p.key() for p in self.proposals]

    def template_file(self):
        template = self.proposal_formatter.prefix(self.competition_name)
        template += "{% for proposal_id in proposal_ids %}\n"
        template += (
            "    {%%- if proposal_id in %s.keys() -%%}\n" % self.competition_name
        )
        template += self.proposal_formatter.format_proposal(
            self.competition_name, "proposal_id"
        )
        template += "{% endif -%}\n"
        template += "{% endfor %}\n"
        template += self.proposal_formatter.suffix()
        return template

    def grouped_data(self):
        return {"proposal_ids": self.keys}


class GeographicToc(Toc):
    """A toc where the grouping is multi level.  For instance, for a given
    competition, we might want to group first by Country, then by State, then
    by County, but for another we might want to group by Region, SubRegion, Country,
    AND State.  This Toc handles all the collating of the data, and then puts
    out the toc in a general way."""

    def __init__(self, name, column_sets):
        super().__init__()
        self.name = name
        self.column_sets = column_sets
        self.num_levels = len(column_sets[0])
        self.data = {}

    def process_competition(self, competition):
        self.competition_name = competition.name

        def add_proposal_to_data(proposal, data, column_set):
            val = proposal.cell(column_set[0]).strip()
            if not val:
                return
            if len(column_set) > 1:
                if val not in data:
                    data[val] = {"shown": False, "subcolumn": {}}
                add_proposal_to_data(proposal, data[val]["subcolumn"], column_set[1:])
            else:
                if val not in data:
                    data[val] = {"shown": False, "proposals": []}
                if proposal.key() not in data[val]["proposals"]:
                    data[val]["proposals"].append(proposal.key())

        if self.proposals is None:
            self.proposals = competition.ordered_proposals()

        for proposal in self.proposals:
            for column_set in self.column_sets:
                add_proposal_to_data(proposal, self.data, column_set)

        def sort_data(data):
            for key in sorted(data.keys()):
                if "subcolumn" in data[key]:
                    data[key]["subcolumn"] = sort_data(data[key]["subcolumn"])

            return {key: data[key] for key in sorted(data.keys())}

        self.data = sort_data(self.data)

    def grouped_data(self):
        return {"groups": self.data}

    def template_file(self):
        template = "__TOC__"
        template += ""
        template += "{%- for subcolumn_name_0, subcolumn_data_0 in groups.items() %}\n"
        for i in range(1, self.num_levels):
            template += (
                '{%%- for subcolumn_name_%s, subcolumn_data_%s in subcolumn_data_%s["subcolumn"].items() %%}\n'
                % (i, i, i - 1)
            )

        template += '{%%- for proposal_id in subcolumn_data_%s["proposals"] -%%}\n' % (
            self.num_levels - 1
        )
        template += "{%% if proposal_id in %s.keys() %%}\n" % self.competition_name
        template += '{%- if not subcolumn_data_0["shown"] -%}\n'
        template += '{%- set _ = subcolumn_data_0.update({"shown": True }) %}\n'
        template += "= {{ subcolumn_name_0 }} =\n"
        for i in range(1, self.num_levels):
            template += "{%- endif -%}\n"
            template += '{%%- if not subcolumn_data_%s["shown"] -%%}\n' % i
            template += (
                '{%%- set _ = subcolumn_data_%s.update({"shown": True }) %%}\n' % i
            )
            template += "%s {{ subcolumn_name_%s }} %s\n" % (
                "=" * (i + 1),
                i,
                "=" * (i + 1),
            )

        template += self.proposal_formatter.prefix(self.competition_name)

        template += "{% endif -%}\n"
        template += self.proposal_formatter.format_proposal(
            self.competition_name, "proposal_id"
        )
        template += "{% endif -%}\n"
        template += "{% endfor %}\n"
        template += self.proposal_formatter.suffix()
        for _ in range(self.num_levels):
            template += "{%- endfor %}\n"

        return template


class RegionAwareGeographicToc(GeographicToc):
    """A special case of the GeographicToc that adds region and subregion data
    to the geographic data.  This region data doesn't belong in the spreadsheet,
    so it's just added to the toc adjacent json file.

    The assumption is that the highest level location value is going to be a country,
    and that's the key to look into the region data."""

    def process_competition(self, competition):
        import importlib.resources as pkg_resources
        from . import data

        super().process_competition(competition)

        region_data_by_country = {}
        csv_reader = csv.reader(
            pkg_resources.open_text(data, "regionconfig.csv", encoding="utf-8"),
            delimiter=",",
            quotechar='"',
        )
        next(csv_reader)
        for row in csv_reader:
            region_data_by_country[row[0]] = {"subregion": row[1], "region": row[2]}

        country_errors = []

        self.num_levels = self.num_levels + 2
        country_data = self.data
        self.data = {}
        for country in country_data.keys():
            try:
                region = region_data_by_country[country]["region"]
                subregion = region_data_by_country[country]["subregion"]
                if region not in self.data:
                    self.data[region] = {"shown": False, "subcolumn": {}}
                if subregion not in self.data[region]["subcolumn"]:
                    self.data[region]["subcolumn"][subregion] = {
                        "shown": False,
                        "subcolumn": {},
                    }
                self.data[region]["subcolumn"][subregion]["subcolumn"][
                    country
                ] = country_data[country]
            except KeyError:
                if country not in country_errors:
                    print(
                        "Country %s not in region config file, skipping" % country,
                        file=sys.stderr,
                    )
                    country_errors.append(country)
