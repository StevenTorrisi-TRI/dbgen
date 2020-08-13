from dbgen import (
    Model,
    Generator,
    Query,
    PyBlock,
    MAX,
    LEN,
    IF_ELSE,
    Literal,
    true,
    false,
    One,
    Zero,
    Expr,
    EQ,
    GT,
)

################################################################################


def analysis(m: Model) -> None:
    ##################
    # Extract tables #
    ##################
    tabs = [
        "scientist",
        "procedures",
        "history",
        "electrode",
        "anode",
        "fuel_cell",
        "element",
        "electrode_composition",
    ]

    (
        Scientist,
        Procedures,
        History,
        Electrode,
        Anode,
        Fuel_cell,
        Element,
        Electrode_compostion,
    ) = map(m.get, tabs)

    rels = [
        History.r("operator"),
        Fuel_cell.r("cathode"),
        Fuel_cell.r("anode"),
        Anode.r("electrode"),
        Electrode.r("sample"),
        History.r("sample"),
        History.r("expt_type"),
    ]
    (
        history__operator,
        fuel_cell__cathode,
        fuel_cell__anode,
        anode__electrode,
        electrode__sample,
        history__sample,
        history__expt_type,
    ) = map(m.get_rel, rels)

    ################
    # ADD TO MODEL #
    ################
    ############################################################################
    ssn_div_desc = (
        "Record whether the sample processing step ID# evenly "
        "divides the ssn of the scientist who processed it, "
        "and only computes this when the procedure name is "
        "greater than three letter long!"
    )

    epath = m.make_path(
        "sample", [electrode__sample, anode__electrode, fuel_cell__anode]
    )
    spath = m.make_path("scientist", [history__operator])
    ppath = m.make_path("procedures", [history__expt_type])

    ssnquery = Query(
        exprs=dict(ssn=Scientist["ssn"](spath), step=History["step"](), h=History.id()),
        basis=["history"],
        constr=GT(LEN(Procedures["procedure_name"](ppath)), Literal(3)),
    )
    ssnpb = PyBlock(
        lambda ssn, step: ssn % step == 0,
        args=[ssnquery["ssn"], ssnquery["step"]],
        outnames=["answer"],
    )

    ssn_divided = Generator(
        name="ssn_divided",
        desc=ssn_div_desc,
        loads=[History(step_divides_ssn=ssnpb["answer"], history=ssnquery["h"])],
        query=ssnquery,
        transforms=[ssnpb],
    )

    ############################################################################

    # Represent whether a battery had a calcinated anode with a SQL expression
    proc_name = Procedures["procedure_name"]

    pp = m.make_path(
        "procedures",
        [
            history__expt_type,
            history__sample,
            electrode__sample,
            anode__electrode,
            fuel_cell__anode,
        ],
    )

    calcined_anode = EQ(proc_name(pp), Literal("Calcination"))

    def bool_to_tinyint(x: Expr) -> Expr:
        """Useful utility function to generate SQL Expression"""
        return IF_ELSE(x, One, Zero)

    def int2bool(x: Expr) -> Expr:
        return IF_ELSE(EQ(x, One), true, false)

    c_query = Query(
        exprs=dict(
            f=MAX(Fuel_cell.id()), calc=int2bool(MAX(bool_to_tinyint(calcined_anode)))
        ),
        basis=["fuel_cell"],
        aggcols=[Fuel_cell["expt_id"]()],
    )  # Aggregate over this object

    fc_act = Fuel_cell(calc_anode=c_query["calc"], fuel_cell=c_query["f"])
    calcined = Generator(
        name="calcined",
        desc="Record whether battery anode was ever calcinated",
        query=c_query,
        loads=[fc_act],
    )

    ############################################################################
    ############################################################################
    ############################################################################

    m.add([ssn_divided, calcined])
