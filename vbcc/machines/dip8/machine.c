#include "supp.h"
static char FILE_[]=__FILE__;

// In this file:
/****************************************/
// Backend setup
// Debug
// Register allocation
// Object load/store/emit
// 
// Code generation
/****************************************/



char cg_copyright[]="vbcc generic code-generator V0.1b (c) in 2001 by Volker Barthelmann";

/*  Commandline-flags the code-generator accepts:
    0: just a flag
    VALFLAG: a value must be specified
    STRINGFLAG: a string can be specified
    FUNCFLAG: a function will be called
    apart from FUNCFLAG, all other versions can only be specified once */
int g_flags[MAXGF]={0,0,
            VALFLAG,VALFLAG,VALFLAG,
            0,0,
            VALFLAG};
/* the flag-name, do not use names beginning with l, L, I, D or U, because
   they collide with the frontend */
char *g_flags_name[MAXGF]={"three-addr","load-store",
               "volatile-gprs","xxx","xxxx",
               "imm-ind","gpr-ind",
               "gpr-args"};
/* the results of parsing the command-line-flags will be stored here */
union ppi g_flags_val[MAXGF];

/* Names of target-specific variable attributes.                */
char *g_attr_name[]={"__interrupt",0};



/****************************************/

#define IMM_IND    ((g_flags[5]&USEDFLAG)?1:0)
#define GPR_IND    ((g_flags[6]&USEDFLAG)?2:0)
#define GPR_ARGS   ((g_flags[7]&USEDFLAG)?g_flags_val[7].l:0)

static FILE *f; // Output file

/* sizes of basic data-types, used to initialize sizetab[] */
static long msizetab[MAX_TYPE+1]={0,1,2,2,2,8,4,8,8,0,2,0,0,0,2,0,0,0};

/* macros defined by the backend */
static char *marray[]={"__section(x)=__vattr(\"section(\"#x\")\")",
               "__GENERIC__",
               0};

#define dt(t) (((t)&UNSIGNED)?udt[(t)&NQ]:sdt[(t)&NQ])
static char *sdt[MAX_TYPE+1]={"??","c","s","i","l","ll","f","d","ld","v","p"};
static char *udt[MAX_TYPE+1]={"??","uc","us","ui","ul","ull","f","d","ld","v","p"};

/* sections */
#define DATA 0
#define BSS 1
#define CODE 2
#define RODATA 3
#define SPECIAL 4

static int section=-1,newobj;
static char *codename="\t.text\n",
  *dataname="\t.data\n",
  *bssname="",
  *rodataname="";//\t.section\t.rodata\n";

static char *ret;       // return instruction (why is this not fixed?)
static int exit_label;  // label at the end of a function

// prefixes for labels and external identifiers
static char *labprefix="l",*idprefix="";
// local labels created by e.g. compare
static char *tmpprefix="b";
static int tmplabel = 0;


static long function_arg_bytes = 0;
static const long spillsize = 2;    // size of stack space for storing spilled reg
static long localsize;              // size of local vars on stack
static long rsavesize,argsize;


static long stackoffset = spillsize;    // sp+stackoffset = start of locals
static unsigned int initial_sp = 0xFEFF;


#define isreg(x) ((p->x.flags&(REG|DREFOBJ))==REG)
#define isconst(x) ((p->x.flags&(KONST|DREFOBJ))==KONST)
#define isvar(x) ((p->x.flags&(VAR|DREFOBJ))==VAR)
#define isflags(obj, f) (((obj)->flags & (f))==(f))
#define islocal(var) (((var)->storage_class == REGISTER)||((var)->storage_class == AUTO))







/*****************************************************************************/
// Backend setup
// register sizes/types/pairs, type sizes, return registers, etc.
/*****************************************************************************/

// Registers:

// register 0 is invalid
char *regnames[]    = { "NA", "x", "y", "bh", "bl", "ch", "cl", "b", "c"};
zmax regsize[]      = { 0,    1, 1, 1, 1, 1, 1, 2, 2}; // size in bytes
int  regsa[]        = { 0,    0, 0, 0, 0, 0, 0, 0, 0}; // 1 if register should not be used by the compiler
int  regscratch[]   = { 0,    1, 1, 1, 1, 1, 1, 1, 1}; /*  Specifies which registers may be scratched by functions.    */

struct Typ rtyp = {CHAR};
struct Typ wtyp = {INT};
struct Typ *regtype[] = { NULL,     // type of each register
    &rtyp, &rtyp, &rtyp, &rtyp, &rtyp, &rtyp, &wtyp, &wtyp
};

/* specifies the priority for the register-allocator, if the same
   estimated cost-saving can be obtained by several registers, the
   one with the highest priority will be used */
int reg_prio[MAXR+1];

/* an empty reg-handle representing initial state */
struct reg_handle empty_reg_handle={0,0};



zmax   t_min[MAX_TYPE+1];
zumax  t_max[MAX_TYPE+1];
zumax tu_max[MAX_TYPE+1];
zmax   align[MAX_TYPE+1];   /*  Alignment-requirements for all types in bytes. */
zmax sizetab[MAX_TYPE+1];   /*  sizes of the basic types (in bytes) */
zmax maxalign = 1;
zmax char_bit = 8;

/*  Does necessary initializations for the code-generator. Gets called  */
/*  once at the beginning and should return 0 in case of problems.      */
int init_cg(void)
{
    /*  Initialize some values which cannot be statically initialized   */
    /*  because they are stored in the target's arithmetic.             */
    stackalign = 1;

    for (int i=0;i<=MAX_TYPE;i++){
        sizetab[i]=l2zm(msizetab[i]);
        align[i] = 1;
    }

    /*  Initialize the min/max-settings. Note that the types of the     */
    /*  host system may be different from the target system and you may */
    /*  only use the smallest maximum values ANSI guarantees if you     */
    /*  want to be portable.                                            */
    /*  That's the reason for the subtraction in t_min[INT]. Long could */
    /*  be unable to represent -2147483648 on the host system.          */
    t_min[CHAR]   =l2zm(-128L);
    t_max[CHAR]   =ul2zum(127L);
    tu_max[CHAR]  =ul2zum(255UL);

    t_min[SHORT]  =l2zm(-32768L);
    t_max[SHORT]  =ul2zum(32767UL);
    tu_max[SHORT] =ul2zum(65535UL);

    t_min[INT]    =t_min[SHORT];
    t_max[INT]    =t_max[SHORT];
    tu_max[INT]   =tu_max[SHORT];

    t_min[LONG]   =zmsub(l2zm(-2147483647L),l2zm(1L));
    t_max[LONG]   =ul2zum(2147483647UL);
    tu_max[LONG]  =ul2zum(4294967295UL);

    t_min[LLONG]  =zmlshift(l2zm(1L),l2zm(63L));
    t_max[LLONG]  =zumrshift(zumkompl(ul2zum(0UL)),ul2zum(1UL));
    tu_max[LLONG] =zumkompl(ul2zum(0UL));
    t_min[MAXINT] =t_min[LLONG];
    t_max[MAXINT] =t_max(LLONG);  
    tu_max[MAXINT]=t_max(UNSIGNED|LLONG);

    target_macros=marray;
    return 1;
}

void cleanup_cg(FILE *f) {}

// Debug
void init_db(FILE *f) {}
void cleanup_db(FILE *f) {
  if (f) section=-1;
}

// Define register pairs: B=BH:BL, C=CH:CL
int reg_pair(int r,struct rpair *p) {

    if (r == REG_B) {
        p->r1 = REG_BH;
        p->r2 = REG_BL;
        return 1;
    } else if (r == REG_C) {
        p->r1 = REG_CH;
        p->r2 = REG_CL;
        return 1;
    }
    return 0;
}

/*  Returns 0 if register r cannot store variables of   */
/*  type t. If t==POINTER and mode!=0 then it returns   */
/*  non-zero only if the register can store a pointer   */
/*  and dereference a pointer to mode.                  */
int regok(int r,int t,int mode) {

    if (r==0) return 0;
    t &= NQ;
    if ((t==CHAR) && (r >= REG_X) && (r <= REG_CL)) return 1;               // 8-bit
    if (((t==SHORT)||(t==INT)||(t==POINTER)) && (r >= REG_B)) return 1;     // 16-bit

    return 0;
}

/*  Returns the register in which variables of type t are returned. */
/*  If the value cannot be returned in a register returns 0.        */
/*  A pointer MUST be returned in a register. The code-generator    */
/*  has to simulate a pseudo register if necessary.                 */
int freturn(struct Typ *t) {
    
    if (ISFLOAT(t->flags)) 
        return 0;
    if (ISSTRUCT(t->flags)||ISUNION(t->flags)) 
        return 0;
    if (zmleq(szof(t),l2zm(2L))) 
        return REG_C;
    else
        return 0;
}

/*  Returns zero if the IC p can be safely executed     */
/*  without danger of exceptions or similar things.     */
/*  vbcc may generate code in which non-dangerous ICs   */
/*  are sometimes executed although control-flow may    */
/*  never reach them (mainly when moving computations   */
/*  out of loops).                                      */
/*  Typical ICs that generate exceptions on some        */
/*  machines are:                                       */
/*      - accesses via pointers                         */
/*      - division/modulo                               */
/*      - overflow on signed integer/floats             */
int dangerous_IC(struct IC *p) {

    int c=p->code;
    if ((p->q1.flags&DREFOBJ)||(p->q2.flags&DREFOBJ)||(p->z.flags&DREFOBJ)) return 1;
    if ((c==DIV||c==MOD)&&!isconst(q2)) return 1;
    return 0;
}

/* estimate the cost-saving if object o from IC p is placed in
   register r */
int cost_savings(struct IC *p, int r, struct obj *o) {

    int c = p->code;

    // Try not to keep things in BH/BL/CH/CL as these are better used as 
    // 16-bit registers
    if (r == REG_BH || r == REG_BL || r == REG_CH || r == REG_CL) return 0;

    if (o->flags & VKONST) return 0;
    if (o->flags & DREFOBJ) return 4;
    if (c==SETRETURN && r==p->z.reg  && !(o->flags&DREFOBJ)) return 3;
    if (c==GETRETURN && r==p->q1.reg && !(o->flags&DREFOBJ)) return 3;
    return 2;
}

/*  Returns zero if code for converting np to type t    */
/*  can be omitted.                                     */
int must_convert(int o, int t, int const_expr) {

    int op = o&NQ, tp = t&NQ;
    if (op == tp) return 0;
    if ((op==INT||op==LONG||op==POINTER)&&(tp==INT||tp==LONG||tp==POINTER)) return 0;
    if (op==DOUBLE&&tp==LDOUBLE) return 0;
    if (op==LDOUBLE&&tp==DOUBLE) return 0;
    return 1;
}





/*****************************************************************************/
// Debug
/*****************************************************************************/

void dbgobj(struct obj o) {
    int f = o.flags;
    if (f & KONST) printf("KONST ");
    if (f & VAR) printf("VAR ");
    //if (f & SCRATCH) printf("SCRATCH ");
    if (f & DREFOBJ) printf("DREF ");
    if (f & REG) printf("REG (%s) ", regnames[o.reg]);
    if (f & VARADR) printf("VARADR ");
    if (f & VAR) {
        printf("[%s]", storage_class_name[o.v->storage_class]);
    }
    printf("\n");
}
void dbgic(struct IC *p) {
    pric2(stdout, p);
    printf("  (code %d)\n", p->code);
    printf(" q1 ");
    dbgobj(p->q1);
    printf(" q2 ");
    dbgobj(p->q2);
    printf(" z  ");
    dbgobj(p->z);
}
void dbgregs(void) {
    printf("regs in use: %s%s%s%s\n",
        regs[REG_X]?"x ":"",
        regs[REG_Y]?"y ":"",
        regs[REG_B]?"b ":"",
        regs[REG_C]?"c ":"");
}





/*****************************************************************************/
// Register allocation
/*****************************************************************************/

static int zreg;
static int zreg_allocated;
static int spilled_reg;

static void spill_reg(int r) {
    
    spilled_reg = r;
    long offs = stackoffset-spillsize;
    if (offs == 0) {
        emit(f, "\tst%s sp\t\t;spill\n", regnames[r]);
    } else {
        emit(f, "\tst%s sp+%d\t\t;spill\n", regnames[r], stackoffset-spillsize);
    }
}
static void unspill_reg(void) {
    
    if (spilled_reg != 0) {
        long offs = stackoffset-spillsize;
        if (offs == 0) {
            emit(f, "\tld%s sp\t\t;unspill\n", regnames[spilled_reg]);
        } else {
            emit(f, "\tld%s sp+%d\t\t;unspill\n", regnames[spilled_reg], stackoffset-spillsize);
        }

        spilled_reg = 0;
    }
}

// Allocate a register for a given type.
// If no registers are free, one will be spilled.
// If spillreg is nonzero, that register will be spilled if necessary.
// (It is assumed that spillreg is adequate for the given type.)
static int allocate_reg_for_type(int t, int spillreg) {

    t &= NQ;
    printf("allocating zreg for type %s, used: x:%d y:%d b:%d c:%d\n", typname[t], regs[REG_X], regs[REG_Y], regs[REG_B], regs[REG_C]);

    // Can't use B or C if one of the constituent 8-bit regs is in use
    int b_used = regs[REG_B] | regs[REG_BL] | regs[REG_BH];
    int c_used = regs[REG_C] | regs[REG_CL] | regs[REG_CH];

    if (t == CHAR) {
        if (!regs[REG_X]) {
            regs[REG_X] = 1;
            return REG_X;
        }
        if (!regs[REG_Y]) {
            regs[REG_Y] = 1;
            return REG_Y;
        }
        if (spillreg == 0) {
            spill_reg(REG_Y);
            return REG_Y;
        }
    }
    if (t == SHORT || t == INT || t == POINTER) {
        if (!b_used) {
            regs[REG_B] = 1;
            return REG_B;
        }
        if (!c_used) {
            regs[REG_C] = 1;
            return REG_C;
        }
        if (spillreg == 0) {
            spill_reg(REG_C);
            return REG_C;
        }
    }

    if (spillreg) {
        spill_reg(spillreg);
        return spillreg;
    }

    printf("type was %d\n", t);
    ierror(0);
}

static void free_reg(int r) {
    regs[r] = 0;
}














/*****************************************************************************/
// Object load/store/emit
/*****************************************************************************/

typedef enum {
    PART_ALL = 0,
    PART_LO,
    PART_HI
} ObjectPart;

static void emit_obj(struct obj *p,int t, int operand);
static void emit_obj_part(struct obj *p,int t, int operand, ObjectPart part);

/* calculate the actual current offset of an object relativ to the
   stack-pointer; we use a layout like this:

   ------------------------------------------------
   | arguments to this function                   |
   ------------------------------------------------
   | return-address [size=2]                      |
   ------------------------------------------------
   | caller-save registers [size=rsavesize]       |
   ------------------------------------------------
   | local variables [size=localsize]             |
   ------------------------------------------------ <-- sp + stackoffset
   | spilled register [size=spillsize]            |
   ------------------------------------------------ <-- sp normally here
   | arguments to called functions [size=argsize] |
   ------------------------------------------------
*/

static long real_offset(struct obj *o)
{
  long off = zm2l(o->v->offset);

  if (off<0) {
    /* function parameter */
    off=localsize+rsavesize+2-off;
  }

  off += stackoffset;
  off += zm2l(o->val.vmax); //??
  return off;
}

/*  Initializes an addressing-mode structure and returns a pointer to
    that object. Will not survive a second call! */
static struct obj *cam(int flags,int base,long offset)
{
  static struct obj obj;
  static struct AddressingMode am;
  obj.am=&am;
  am.flags=flags;
  am.base=base;
  am.offset=offset;
  return &obj;
}

// Load the address of a variable into register r
static void load_address(int r,struct obj *o,int type) {

    if (!isflags(o, VAR)) ierror(0);

    if (islocal(o->v)) {
        // SP + offset
        long off = real_offset(o);
        emit(f,"\tmov   %s, %s\n",regnames[r],"sp");
        if (off) emit(f,"\taddw\t%s, #%ld\n", regnames[r], off);
    } else {
        // Static address
        emit(f,"\tmov   %s, #", regnames[r]);
        emit_obj(o,type,0);
        emit(f,"\n");
    }
}


// Load object into register
static void load_reg(int r,struct obj *o,int type)
{
  type&=NU;
  if (o->flags&VARADR) {
    load_address(r,o,POINTER);
  } else {
    if ((o->flags&(REG|DREFOBJ))==REG&&o->reg==r) return;

    // Move from another register
    if ((isflags(o, REG) && !isflags(o, DREFOBJ))) {
        if (regsize[r] == 2 && regsize[o->reg] == 1) {
            // Moving 8 bit into 16 bit
            struct rpair rp;
            if (!reg_pair(r, &rp)) ierror(0);
            emit(f, "\tmov   %s, %s\n", regnames[rp.r2], regnames[o->reg]);
            emit(f, "\tmov   %s, #0\n", regnames[rp.r1]);
            return;
        } else if (regsize[r] == 1 && regsize[o->reg] == 2) {
            // Moving 16 bit into 8 bit - truncate
            struct rpair rp;
            if (!reg_pair(o->reg, &rp)) ierror(0);
            emit(f, "\tmov   %s, %s\n", regnames[r], regnames[rp.r2]);
            return;
        }
        // Same width
        emit(f, "\tmov   %s, %s\n", regnames[r], regnames[o->reg]);
        return;
    }

    // Load literal
    if (isflags(o, KONST) && !isflags(o, DREFOBJ)) {
        emit(f, "\tmov   %s, #", regnames[r]);
        emitval(f, &o->val, type);
        emit(f,"\n");
        return;
    }

    emit(f, "\tld%s   ", regnames[r]);
    emit_obj(o,type,0);
    emit(f,"\n");
  }
}

// Store register into object
static void store_reg(int r,struct obj *o,int type) {

    int oisreg = isflags(o, REG) && !isflags(o, DREFOBJ);

    if (oisreg) {
        if (o->reg == r) return; // Same register

        emit(f, "\tmov   %s, %s\n", regnames[o->reg], regnames[r]);
        return;
    }



    type&=NQ;
    emit(f, "\tst%s   ", regnames[r]);
    emit_obj(o,type,0);
    emit(f,"\n");
}




static void emit_obj(struct obj *p,int t, int operand) {
    emit_obj_part(p, t, operand, PART_ALL);
}

static void emit_reg_part(int reg, ObjectPart part) {

    struct rpair rp;
    if (reg_pair(reg, &rp)) {
        // Convert b/c into bh,bl,ch,cl
        if (part == PART_HI) reg = rp.r1;
        if (part == PART_LO) reg = rp.r2;
    }
    emit(f, "%s", regnames[reg]);

}

// Print an object:
// its value, if it is a constant
// its name, if it is a register
// its address, otherwise
// if part == PART_HI or PART_LO, just print the (address/name of the) upper or lower 8 bits of the object.
static void emit_obj_part(struct obj *p,int t, int operand, ObjectPart part) {

    // Literal value
    if (isflags(p, KONST) && !isflags(p, DREFOBJ)){
        emit(f, "#");
        if (part == PART_ALL) {
            emitval(f,&p->val,t&NU);
        } else if (part == PART_LO) {
            // Low byte
            eval_const(&p->val, t);
            unsigned char byte = vmax & 0xFF;
            emit(f, "$%02x", byte);
        } else if (part == PART_HI) {
            // High byte
            eval_const(&p->val, t);
            unsigned char byte = (vmax >> 8) & 0xFF;
            emit(f, "$%02x", byte);
        }
        return;
    }

    // Register
    if (isflags(p, REG) && !isflags(p, DREFOBJ)) {
        int reg = p->reg;
        emit_reg_part(reg, part);
        return;
    }

    // If we are the operand of an ALU instruction,
    // addresses need to be bracketed with [ ]
    if (operand) emit(f, "[");


    // Addressing modes? FIXME
    if (p->am) {
        if(p->am->flags&GPR_IND) emit(f,"(%s,%s)",regnames[p->am->offset],regnames[p->am->base]);
        if(p->am->flags&IMM_IND) emit(f,"(%ld,%s)",p->am->offset,regnames[p->am->base]);
        return;
    }

    // Absolute address
    if (isflags(p, KONST|DREFOBJ)) {
        eval_const(&p->val, p->dtyp & NU);
        if (part == PART_HI) vmax++;
        emit(f, "$%02x", vmax);
    }

    // Register indirect
    else if (isflags(p, REG|DREFOBJ)) {
        emit(f,"%s",regnames[p->reg]);
        if (part == PART_HI) emit(f, "+1"); // Use "reg+imm8" addressing mode
    }

    else {

        // Memory indirect
        if (p->flags&DREFOBJ) emit(f,"*");

        if (p->flags&VAR) {

            // Local (stack-addressed)
            if(p->v->storage_class==AUTO||p->v->storage_class==REGISTER) {
                int offset = real_offset(p);
                if (part == PART_HI) offset++;
                emit(f,"sp+%ld", offset);

            } else {
                if (!zmeqto(l2zm(0L),p->val.vmax)){emitval(f,&p->val,LONG);emit(f,"+");} // FIXME: what is this
                if(p->v->storage_class==STATIC){
                    int addr = zm2l(p->v->offset);
                    emit(f,"%s%ld", labprefix, addr);
                    if (part == PART_HI) emit(f, "+1"); // Assembler will add one to address
                }else{
                    emit(f,"%s%s",idprefix,p->v->identifier);
                    if (part == PART_HI) emit(f, "+1"); // Assembler will add one to address
                }
            }
        }
    }

    if (operand) emit(f, "]");

}
































/*  Yields log2(x)+1 or 0. */
static long pof2(zumax x)
{
  zumax p;int ln=1;
  p=ul2zum(1L);
  while(ln<=32&&zumleq(p,x)){
    if(zumeqto(x,p)) return ln;
    ln++;p=zumadd(p,p);
  }
  return 0;
}


static struct IC *preload(FILE *,struct IC *);

static void function_top(FILE *,struct Var *,long);
static void function_bottom(FILE *f,struct Var *,long);

// (assuming unsigned)
// carry set --> greater than or equal
// carry clr --> less than 

static char *ccs[]={"z","nz","cc","cs","le","gt",""};
static char *logicals[]={"or","xor","and"};
static char *arithmetics[]={"shl","shr","add","sub","mul","div","mod"};


  //printf("preload %d %d %d\n", q1reg, q2reg, zreg);
  
  // if((p->q1.flags&(DREFOBJ|REG))==DREFOBJ&&!p->q1.am){
  //   p->q1.flags&=~DREFOBJ;
  //   load_reg(f,t1,&p->q1,q1typ(p));
  //   p->q1.reg=t1;
  //   p->q1.flags|=(REG|DREFOBJ);
  // }

  // if(p->q1.flags&&LOAD_STORE&&!isreg(q1)){
  //   if(ISFLOAT(q1typ(p)))
  //     q1reg=t1;
  //   else
  //     q1reg=t1;
  //   load_reg(f,q1reg,&p->q1,q1typ(p));
  //   p->q1.reg=q1reg;
  //   p->q1.flags=REG;
  // }

  // if((p->q2.flags&(DREFOBJ|REG))==DREFOBJ&&!p->q2.am){
  //   p->q2.flags&=~DREFOBJ;
  //   load_reg(f,t1,&p->q2,q2typ(p));
  //   p->q2.reg=t1;
  //   p->q2.flags|=(REG|DREFOBJ);
  // }

  // if(p->q2.flags&&LOAD_STORE&&!isreg(q2)){
  //   if(ISFLOAT(q2typ(p)))
  //     q2reg=t2;
  //   else
  //     q2reg=t2;
  //   load_reg(f,q2reg,&p->q2,q2typ(p));
  //   p->q2.reg=q2reg;
  //   p->q2.flags=REG;
  // }

/* save the result (in zreg) into p->z */
void save_result(struct IC *p)
{
  // if((p->z.flags&(REG|DREFOBJ))==DREFOBJ&&!p->z.am){
  //   p->z.flags&=~DREFOBJ;
  //   load_reg(f,t2,&p->z,POINTER);
  //   p->z.reg=t2;
  //   p->z.flags|=(REG|DREFOBJ);
  // }
  if (isreg(z)) {
    if (p->z.reg != zreg) emit(f, "\tmov.%s\t%s,%s\n",dt(ztyp(p)),regnames[p->z.reg],regnames[zreg]);
  } else {
    store_reg(zreg,&p->z,ztyp(p));
  }

}



/*  Test if there is a sequence of FREEREGs containing FREEREG reg.
    Used by peephole. */
static int exists_freereg(struct IC *p,int reg)
{
  while(p&&(p->code==FREEREG||p->code==ALLOCREG)){
    if(p->code==FREEREG&&p->q1.reg==reg) return 1;
    p=p->next;
  }
  return 0;
}

/* search for possible addressing-modes */
static void peephole(struct IC *p)
{
  int c,c2,r;struct IC *p2;struct AddressingMode *am;

  for (;p;p=p->next) {
    c=p->code;
    if(c!=FREEREG&&c!=ALLOCREG&&(c!=SETRETURN||!isreg(q1)||p->q1.reg!=p->z.reg)) exit_label=0;
    if(c==LABEL) exit_label=p->typf;

    /* Try const(reg) */
    if (IMM_IND&&(c==ADDI2P||c==SUBIFP)&&isreg(z)&&(p->q2.flags&(KONST|DREFOBJ))==KONST){
        int base;zmax of;struct obj *o;
        printf("eval\n");
        eval_const(&p->q2.val,p->typf);
        if (c==SUBIFP) of=zmsub(l2zm(0L),vmax); else of=vmax;
        if (1/*zmleq(l2zm(-32768L),vmax)&&zmleq(vmax,l2zm(32767L))*/){
            r=p->z.reg;
            if(isreg(q1)) base=p->q1.reg; else base=r;
            o=0;
            for(p2=p->next;p2;p2=p2->next){
                c2=p2->code;
                if(c2==CALL||c2==LABEL||(c2>=BEQ&&c2<=BRA)) break;
                if(c2!=FREEREG&&(p2->q1.flags&(REG|DREFOBJ))==REG&&p2->q1.reg==r) break;
                if(c2!=FREEREG&&(p2->q2.flags&(REG|DREFOBJ))==REG&&p2->q2.reg==r) break;
                if(c2!=CALL&&(c2<LABEL||c2>BRA)/*&&c2!=ADDRESS*/){
                    if(!p2->q1.am&&(p2->q1.flags&(REG|DREFOBJ))==(REG|DREFOBJ)&&p2->q1.reg==r){
                      if(o) break;
                      o=&p2->q1;
                    }
                    if(!p2->q2.am&&(p2->q2.flags&(REG|DREFOBJ))==(REG|DREFOBJ)&&p2->q2.reg==r){
                      if(o) break;
                      o=&p2->q2;
                    }
                    if(!p2->z.am&&(p2->z.flags&(REG|DREFOBJ))==(REG|DREFOBJ)&&p2->z.reg==r){
                      if(o) break;
                      o=&p2->z;
                    }
                }
                if(c2==FREEREG||(p2->z.flags&(REG|DREFOBJ))==REG){
                    int m;
                    if(c2==FREEREG)
                      m=p2->q1.reg;
                    else
                      m=p2->z.reg;
                    if(m==r){
                      if(o){
                    o->am=am=mymalloc(sizeof(*am));
                    am->flags=IMM_IND;
                    am->base=base;
                    am->offset=zm2l(of);
                    if(isreg(q1)){
                      p->code=c=NOP;p->q1.flags=p->q2.flags=p->z.flags=0;
                    }else{
                      p->code=c=ASSIGN;p->q2.flags=0;
                      p->typf=p->typf2;p->q2.val.vmax=sizetab[p->typf2&NQ];
                    }
                      }
                      break;
                    }
                    if(c2!=FREEREG&&m==base) break;
                    continue;
                }
            }
        }
    }

    /* Try reg,reg */
    if (GPR_IND&&c==ADDI2P&&isreg(q2)&&isreg(z)&&(isreg(q1)||p->q2.reg!=p->z.reg)) {
        printf("reg,reg\n");
        int base,idx;struct obj *o;
        r=p->z.reg;idx=p->q2.reg;
        if(isreg(q1)) base=p->q1.reg; else base=r;
        o=0;
        for(p2=p->next;p2;p2=p2->next){
            c2=p2->code;
            if(c2==CALL||c2==LABEL||(c2>=BEQ&&c2<=BRA)) break;
            if(c2!=FREEREG&&(p2->q1.flags&(REG|DREFOBJ))==REG&&p2->q1.reg==r) break;
            if(c2!=FREEREG&&(p2->q2.flags&(REG|DREFOBJ))==REG&&p2->q2.reg==r) break;
            if((p2->z.flags&(REG|DREFOBJ))==REG&&p2->z.reg==idx&&idx!=r) break;
        
            if(c2!=CALL&&(c2<LABEL||c2>BRA)/*&&c2!=ADDRESS*/){
              if(!p2->q1.am&&(p2->q1.flags&(REG|DREFOBJ))==(REG|DREFOBJ)&&p2->q1.reg==r){
                if(o||(q1typ(p2)&NQ)==LLONG) break;
                o=&p2->q1;
              }
              if(!p2->q2.am&&(p2->q2.flags&(REG|DREFOBJ))==(REG|DREFOBJ)&&p2->q2.reg==r){
                if(o||(q2typ(p2)&NQ)==LLONG) break;
                o=&p2->q2;
              }
              if(!p2->z.am&&(p2->z.flags&(REG|DREFOBJ))==(REG|DREFOBJ)&&p2->z.reg==r){
                if(o||(ztyp(p2)&NQ)==LLONG) break;
                o=&p2->z;
              }
            }
            if(c2==FREEREG||(p2->z.flags&(REG|DREFOBJ))==REG){
              int m;
              if(c2==FREEREG)
                m=p2->q1.reg;
              else
                m=p2->z.reg;
              if(m==r){
                if(o){
                  o->am=am=mymalloc(sizeof(*am));
                  am->flags=GPR_IND;
                  am->base=base;
                  am->offset=idx;
              if(isreg(q1)){
            p->code=c=NOP;p->q1.flags=p->q2.flags=p->z.flags=0;
              }else{
            p->code=c=ASSIGN;p->q2.flags=0;
            p->typf=p->typf2;p->q2.val.vmax=sizetab[p->typf2&NQ];
              }
                }
                break;
              }
              if(c2!=FREEREG&&m==base) break;
              continue;
            }
      }
    }
  }
}



/* changes to a special section, used for __section() */
static int special_section(FILE *f,struct Var *v)
{
  char *sec;
  if (!v->vattr) return 0;
  sec = strstr(v->vattr,"section(");
  if (!sec) return 0;
  sec += strlen("section(");
  emit(f,"\t.section\t");
  while (*sec&&*sec!=')') emit_char(f,*sec++);
  emit(f,"\n");
  if (f) section=SPECIAL;
  return 1;
}

/* generates the function entry code */
static void function_top(FILE *f,struct Var *v,long offset) {
    rsavesize=0;

    emit(f, "\n");
    
    if (!special_section(f,v)&&section!=CODE) {
        emit(f,codename);
        if(f) section=CODE;
    }

    if (v->storage_class==EXTERN) {
        if ((v->flags&(INLINEFUNC|INLINEEXT))!=INLINEFUNC) {
            // Global
            //emit(f,"\t.global\t%s%s\n",idprefix,v->identifier);
        }

        // Label
        emit(f, "%s%s\n",idprefix,v->identifier);

    } else {
        emit(f,"%s%ld\n",labprefix,zm2l(v->offset));
    }

    emit(f, "\tsubsp #%d\n", offset);

}
/* generates the function exit code */
static void function_bottom(FILE *f,struct Var *v,long offset) {
    
    emit(f, "\taddsp #%d\n", offset);
    emit(f,ret);
}







































/*****************************************************************************/
//

// If the result is not a register, allocate one that we can temporarily use
// to store the result, before writing it back
static void allocate_result_reg(struct IC *p, int spillreg) {

    if (isreg(z)) {
        zreg=p->z.reg;
    } else {
        zreg = allocate_reg_for_type(ztyp(p), spillreg);
        zreg_allocated = 1;
        printf("Allocated register %s for result\n", regnames[zreg]);
    }
}

static void free_result_reg(void) {
    if (zreg_allocated) {
        zreg_allocated = 0;
        free_reg(zreg);
    }
    if (spilled_reg) {
        regs[spilled_reg] = 1; // Register is still in use
        unspill_reg();
    }
}

/*****************************************************************************/






// store literal
// stl #L, addr
static void emit_stl(struct IC *p) {
    emit(f, "\tstl   #");
    emitval(f, &p->q1.val, p->typf); // literal
    emit(f, ", ");
    emit_obj(&p->z, p->typf, 0); // address
    emit(f, "\n");
}

// compare
// cmp x, y
static void emit_cmp(struct IC *p, int code, ObjectPart part) {

    int t = p->typf;
    int typesize = sizetab[t & NQ];

    emit(f,"\tcmp   ");
    emit_obj_part(&p->q1, t, 1, part);
    emit(f, ", ");
    if (code == COMPARE) {
        emit_obj_part(&p->q2, t, 1, part);
    } else if (code == TEST) { // Test is compare against zero
        emit(f, "#0");
    }
    emit(f, "\n");

}



static void compare(struct IC *p, int code) {

    int t = p->typf;
    int typesize = sizetab[t & NQ];

    if (typesize > 2) ierror(0);

    if (typesize == 2) {
        // 16 bit compare
        if (!(t & UNSIGNED)) emit(f, "\tsig\n");
        emit_cmp(p, code, PART_HI);
        emit(f, "\tjnz   %s%d\n", tmpprefix, tmplabel);
        emit_cmp(p, code, PART_LO);
        emit(f, "%s%d\n", tmpprefix, tmplabel++);
    } else {
        // 8 bit compare
        if (!(t & UNSIGNED)) emit(f, "\tsig\n");
        emit_cmp(p, code, PART_ALL);
    }

}

// load / store / move
static void assign(struct IC *p) {

    int type = p->typf;
    int nqtype = type & NQ;

    printf("assign\n");

    // Store register into variable
    // Could be memory or another register
    if (isreg(q1) && isvar(z)) {
        store_reg(p->q1.reg, &p->z, regtype[p->q1.reg]->flags);
        return;
    }

    // Store literal
    if (isconst(q1) &&!isreg(z)) {
        if (nqtype == CHAR) {
            // Can be stored to as long as it's not a register
            //if (isvar(z) || isflags(&p->z, KONST|DREFOBJ) || isflags(&p->z, )) {
                emit_stl(p);
                return;
            //}
        }
    }

    allocate_result_reg(p, 0);
    load_reg(zreg, &p->q1, type);
    save_result(p);

}

void print_obj(struct obj a) {
    probj(stdout, &a, 0);
    printf("flags:%x\n", a.flags);
    printf("reg:%d\n", a.reg);
    printf("dtyp:%d\n", a.dtyp);
    printf("val:%ld\n", a.val.vullong);
    printf("stclass:%d\n", a.v->storage_class);
    printf("offset:%ld\n", a.v->offset);
    printf("ident:%s\n", a.v->identifier);
    printf("descr:%s\n\n", a.v->description);
}

static int objs_equal(struct obj a, struct obj b) {
    // A simple memcmp does not detect objects that are actually equal

    if (a.flags != b.flags) return 0;
    if (a.flags & DREFOBJ) {
        // Only compare dtyp for actual pointers
        if (a.dtyp != b.dtyp) return 0;    
    }

    if (a.reg != b.reg) return 0;
    if (a.val.vullong   != b.val.vullong)   return 0;
    if (a.flags&VAR) {
        if (a.v->storage_class != b.v->storage_class) return 0;
        if (a.flags&REG) {
            //fprintf(f,"+%s",regnames[p->reg]);
        } else if (a.v->storage_class==AUTO||a.v->storage_class==REGISTER) {
            if (a.v->offset != b.v->offset) return 0;
        } else {
            if (a.v->storage_class==STATIC) {
                if (a.v->offset != b.v->offset) return 0;
            } else {
                if (strcmp(a.v->identifier, b.v->identifier)) return 0;
            }
        }
        if (a.v->identifier && b.v->identifier) {
            if (strcmp(a.v->identifier, b.v->identifier)) return 0;
        }
        else if (a.v->description && b.v->description)
            if (strcmp(a.v->description, b.v->description)) return 0;
        else {}
            //fprintf(f,"(%p)",(void *)p->v);
        if (a.v->reg && b.v->reg) {
            if (a.v->reg != b.v->reg) return 0;
        }
    }

    return 1;
}

// Return 1 if q1 is a register and the next IC is "freereg q1"
static int q1_can_be_overwritten(struct IC *p) {
    if (p->next && p->next->code == FREEREG) {
        if (isreg(q1) && ((p->next->q1.flags&(REG|DREFOBJ))==REG)) {
            if (p->next->q1.reg == p->q1.reg) {
                return 1;
            }
        }
    }
    return 0;
}

static void emit_arith_operand(struct IC *p, int two_operands, ObjectPart part) {
    int t = p->typf;
    if (two_operands) {
        emit_obj_part(&p->q1, t, 1, part);
    } else {
        emit_reg_part(zreg, part);
    }
}

static void arithmetic(struct IC *p, int code) {

    int t = p->typf;
    int typesize = sizetab[t & NQ];
    int two_operands = 0;

    // If Z == Q1, the instruction is of the form Z = Z op Q2
    // and we don't need a temporary result register
    if (objs_equal(p->z, p->q1)) {
        two_operands = 1;
    }
    printf("arith typesize=%d, 2op=%d\n", typesize, two_operands);

    /* Z = Q1 op Q2
       options:
       (note that mov can be a load or store)

       (1) op  Z, Q2        (if Z == Q1)

       (2) mov Z, Q1        (if Z is a register)
           op  Z, Q2

       (3) op  Q1, Q2       (if Q1 can be overwritten)
           mov Z, Q1
      
       (4) mov Rtemp, Q1    (in general)
           op  Rtemp, Q2
           mov Z, Rtemp
    */

    /* Z = Q1 op Q2
       turn into:
        Rz = Q1
        Rz = Rz op Q2
        Z  = Rz

       If Z is a register then it will be used for Rz.
       If Q1 is a register, it can be used for Rz IFF the next IC is "freereg Q1".
       If Q1 is a register, it will be spilled in the case that a spill is needed.

       FIXME: what about types that don't fit in registers?
    */
    if (!two_operands) {
        // Allocate a result register (or use Z)
        // If Q1 is a register, spill and use that if necessary
        int spillreg = 0;
        if (isreg(z)) {
            // Z is a register - use that
            zreg = p->z.reg;
        } else if (isreg(q1) && q1_can_be_overwritten(p)) {
            printf("Can overwrite q1.\n");
            // Q1 is a register and about to be freed - use that
            zreg = p->q1.reg;
        } else {
            // Have to allocate a temporary result register
            // Prefer to use Q1 if a spill is necessary
            if (isreg(q1)) spillreg = p->q1.reg;
            allocate_result_reg(p, spillreg);            
        }

        // Load first operand into result register
        load_reg(zreg,&p->q1,t);
    }

    // Emit instruction

    if (code == RSHIFT) {
        // Logical shift right
        if (!isconst(q2)) ierror(0); // Only support shifting by a constant for now
        int bits = p->q2.val.vmax;
        emit(f, "\tsig\n"); // Clear carry
        // Rotate
        for (int i=0; i<bits; i++) {
            emit(f, "\tror ");
            emit_arith_operand(p, two_operands, PART_ALL);
            emit(f, "\n");
        }
        // Mask off high bits
        int mask = (1 << bits) - 1;
        emit(f, "\tand ");
        emit_arith_operand(p, two_operands, PART_ALL);
        emit(f, ", #$%02x\n", mask);

    } else {

        if (code>=OR && code<=AND) {
            if (typesize == 2) {
                // Split into two 8-bit operations
                emit(f,"\t%s   ", logicals[code-OR]);
                emit_arith_operand(p, two_operands, PART_LO);
                emit(f, ", ");
                emit_obj_part(&p->q2, t, 1, PART_LO);
                emit(f, "\n");

                emit(f,"\t%s   ", logicals[code-OR]);
                emit_arith_operand(p, two_operands, PART_HI);
                emit(f, ", ");
                emit_obj_part(&p->q2, t, 1, PART_HI);
                emit(f, "\n");                
            } else {
                emit(f,"\t%s   ", logicals[code-OR]);
                // Emit operands
                emit_arith_operand(p, two_operands, PART_ALL);
                emit(f, ", ");
                emit_obj(&p->q2, t, 1);
                emit(f, "\n");                
            }
        } else {
            emit(f,"\t%s%s  ", arithmetics[code-LSHIFT], typesize == 2 ? "w": " ");
            // Emit operands
            emit_arith_operand(p, two_operands, PART_ALL);
            emit(f, ", ");
            emit_obj(&p->q2, t, 1);
            emit(f, "\n");
        }


    }
    
    
    if (!two_operands) {
        save_result(p);
    }

}











































/*****************************************************************************/
// Code generation

static void entry(void) {
    emit(f, "\n");
    emit(f, "\t;bare-metal setup\n");
    emit(f, "\t.varstart $4000\n");
    emit(f, "\tmov b, #%d\n", initial_sp);
    emit(f, "\tmov sp, b\n");
    emit(f, "\tcall main\n");
    emit(f, "\tbrk\n");
    emit(f, "\n");
}




/*  This function has to create <size> bytes of storage */
/*  initialized with zero.                              */
// TODO
void gen_ds (FILE *f,zmax size,struct Typ *t) {
    
    if (newobj && section != SPECIAL) {
        emit(f, "%ld\n", zm2l(size));
    } else {
        emit(f, "\t.space\t%ld\n", zm2l(size));
    }
    newobj=0;
}

void gen_align(FILE *f,zmax align) {}

void gen_var_head(FILE *f,struct Var *v)
/*  This function has to create the head of a variable  */
/*  definition, i.e. the label and information for      */
/*  linkage etc.                                        */
{
    int constflag;char *sec;
    if (v->clist) constflag=is_const(v->vtyp);
    if (v->storage_class==STATIC) {
        if (ISFUNC(v->vtyp->flags)) return;
        if (!special_section(f,v)) {
            if(v->clist&&(!constflag||(g_flags[2]&USEDFLAG))&&section!=DATA){emit(f,dataname);if(f) section=DATA;}
            if(v->clist&&constflag&&!(g_flags[2]&USEDFLAG)&&section!=RODATA){emit(f,rodataname);if(f) section=RODATA;}
            if(!v->clist&&section!=BSS){emit(f,bssname);if(f) section=BSS;}
        }
        if (v->clist||section==SPECIAL) {
            gen_align(f,falign(v->vtyp));
            emit(f,"%s%ld\n",labprefix,zm2l(v->offset));
        } else {
            emit(f,"\t.lcomm\t%s%ld,",labprefix,zm2l(v->offset));
        }
        newobj=1;
    }
  
    if (v->storage_class==EXTERN) {
        emit(f,"\t.global\t%s%s\n",idprefix,v->identifier);
        if (v->flags&(DEFINED|TENTATIVE)) {
            if (!special_section(f,v)) {
                if (v->clist&&(!constflag||(g_flags[2]&USEDFLAG))&&section!=DATA) { 
                    emit(f,dataname);if(f) section=DATA;
                }
                if (v->clist&&constflag&&!(g_flags[2]&USEDFLAG)&&section!=RODATA) {
                    emit(f,rodataname);if(f) section=RODATA;
                }
                if (!v->clist&&section!=BSS){emit(f,bssname);if(f) section=BSS;}
            }
            if (v->clist||section==SPECIAL) {
                gen_align(f,falign(v->vtyp));
                emit(f,"%s%s\n",idprefix,v->identifier);
            } else {
                emit(f,"%s%s = .var ",idprefix,v->identifier);
            }
            newobj=1;
        }
    }
}



// Create static and initialised storage
void gen_dc(FILE *f,int t,struct const_list *p) {

    int type = t & NQ;

    if (type == CHAR) {
        emit(f, "\t.byte\t");
    } else if (type == INT || type == SHORT || type == POINTER) {
        emit(f, "\t.word\t");
    } else {
        ierror(0);
    }

    if (!p->tree) {
        if (ISFLOAT(t)) {
            //
        } else {
            emitval(f,&p->val,t&NU);
        }
    } else {
        emit_obj(&p->tree->o,t&NU, 0);
    }
    emit(f,"\n");newobj=0;
}



// Return 1 if the operation c can be done with type t (char or short), avoiding the need
// to promote to int
int shortcut(int c,int t) {
    if (c==COMPARE||c==ADD||c==SUB||c==AND||c==OR||c==XOR||c==RSHIFT||c==LSHIFT) return 1;
    return 0;
}

/*  The main code-generation routine.                   */
/*  f is the stream the code should be written to.      */
/*  p is a pointer to a doubly linked list of ICs       */
/*  containing the function body to generate code for.  */
/*  v is a pointer to the function.                     */
/*  offset is the size of the stackframe the function   */
/*  needs for local variables.                          */

void gen_code(FILE *file, struct IC *p, struct Var *v, zmax offset) {

    f = file;
    printf("gen_code, offset=%lu\n", offset);
    localsize = zm2l(offset);

    int line_prev = 0;
    int c, t, i;
    struct IC *m;
    argsize = 0;
    for (c=1;c<=MAXR;c++) regs[c]=regsa[c];
    ret = "\tret\n";

    entry();

    // Initial pass (optimise ICs)
    for (m=p;m;m=m->next) {
        c = m->code;
        t = m->typf & NU;

        if (c==ALLOCREG) {regs[m->q1.reg]=1; continue;}
        if (c==FREEREG)  {regs[m->q1.reg]=0; continue;}

        /* convert MULT/DIV/MOD with powers of two */
        if ((t&NQ)<=LONG&&(m->q2.flags&(KONST|DREFOBJ))==KONST&&(t&NQ)<=LONG&&(c==MULT||((c==DIV||c==MOD)&&(t&UNSIGNED)))) {
            eval_const(&m->q2.val,t);
            i=pof2(vmax);
            if (i) {
                if (c==MOD) {
                    vmax=zmsub(vmax,l2zm(1L));
                    m->code=AND;
                } else {
                    vmax=l2zm(i-1);
                    if(c==DIV) m->code=RSHIFT; else m->code=LSHIFT;
                }
                c=m->code;
                gval.vmax=vmax;
                eval_const(&gval,MAXINT);
                if (c==AND) {
                    insert_const(&m->q2.val,t);
                } else {
                    insert_const(&m->q2.val,INT);
                    p->typf2=INT;
                }
            }
        }
    }
    peephole(p);

    for (c=1;c<=MAXR;c++) {
        if (regsa[c]||regused[c]) {
            BSET(regs_modified,c);
        }
    }


    const long stacksize = localsize + spillsize;
    function_top(f, v, stacksize);

    // Code generation pass

    for (;p;p=p->next) {

        c=p->code;t=p->typf;
        free_result_reg();

        printf("\n\n**********************\n");
        dbgic(p);

        // // Interleave source code
        // if (p->line) {
        //     if (p->line != line_prev) emit(f, "; file %s line %d\n", p->file, p->line);
        //     line_prev = p->line;
        // }

        if(c==MOVETOREG){
          load_reg(p->z.reg,&p->q1,regtype[p->z.reg]->flags);
          continue;
        }
        if(c==MOVEFROMREG){
          store_reg(p->z.reg,&p->q1,regtype[p->z.reg]->flags);
          continue;
        }
        if((c==ASSIGN||c==PUSH)&&((t&NQ)>POINTER||((t&NQ)==CHAR&&zm2l(p->q2.val.vmax)!=1))){
          ierror(0);
        }


        if (c==CALL) {
            int reg;
          /*FIXME*/
#if 0      
          if(stack_valid&&(p->q1.flags&(VAR|DREFOBJ))==VAR&&p->q1.v->fi&&(p->q1.v->fi->flags&ALL_STACK)){
        if(framesize+zum2ul(p->q1.v->fi->stack1)>stack)
          stack=framesize+zum2ul(p->q1.v->fi->stack1);
          }else
        stack_valid=0;
#endif
            if ((p->q1.flags&(VAR|DREFOBJ))==VAR&&p->q1.v->fi&&p->q1.v->fi->inline_asm) {
                // Inline asm uses the "call" IC?
                emit_inline_asm(f,p->q1.v->fi->inline_asm);
            } else {
                // Regular function call
                emit(f,"\tcall  ");
                emit_obj(&p->q1,t, 0);
                emit(f,"\n");
            }
            if ((p->q1.flags&(VAR|DREFOBJ))==VAR&&p->q1.v->fi&&(p->q1.v->fi->flags&ALL_REGS)) {
                bvunite(regs_modified,p->q1.v->fi->regs_modified,RSIZE);
            } else {
                int i;
                for (i=1;i<=MAXR;i++) {
                    if(regscratch[i]) BSET(regs_modified,i);
                }
            }

            emit(f, "\taddsp #%d\n", function_arg_bytes);
            stackoffset -= function_arg_bytes;
            function_arg_bytes = 0;
            continue;
        }    


        // Add/sub pointer instructions just become add/sub
        if(c==SUBPFP) c=SUB;
        if(c==ADDI2P) c=ADD;
        if(c==SUBIFP) c=SUB;

        zreg = 0;

        switch (c) {
            case NOP:
                p->z.flags = 0;
                continue;
            case LABEL:
                emit(f,"%s%d\n",labprefix,t);
                continue;                

            // Mark register as used/free
            case ALLOCREG:
                regs[p->q1.reg]=1;dbgregs();
                continue;
            case FREEREG:
                regs[p->q1.reg]=0;dbgregs();
                continue;

            case ASSIGN:
                if (t == 0) ierror(0);
                assign(p);
                continue;                

            // Branch

            case BRA:
                emit(f,"\tjmp\t%s%d\n",labprefix,t);
                continue;

            case BEQ:
                emit(f,"\tjz    %s%d\n", labprefix, t); continue;
            case BNE:
                emit(f,"\tjnz   %s%d\n", labprefix, t); continue;
            case BLT:
                emit(f,"\tjcc   %s%d\n", labprefix, t); continue;
            case BGE:
                emit(f,"\tjcs   %s%d\n", labprefix, t); continue;
            case BLE:
                emit(f,"\tjcc   %s%d\n", labprefix, t);             // less than
                emit(f,"\tjz    %s%d\n", labprefix, t); continue;   // equal
            case BGT:
                emit(f,"\tjz    %s%d\n", tmpprefix, tmplabel);      // not equal, and
                emit(f,"\tjcs   %s%d\n", labprefix, t);             // greater than or equal
                emit(f, "%s%d\n", tmpprefix, tmplabel++);
                continue;




            case CONVERT:
                if (ISFLOAT(q1typ(p))||ISFLOAT(ztyp(p))) ierror(0);

                allocate_result_reg(p, 0);
                load_reg(zreg,&p->q1,t);
                if (sizetab[q1typ(p)&NQ]<sizetab[ztyp(p)&NQ]) {
                    if (q1typ(p) & UNSIGNED) {
                        //emit(f,"\t;zext\t%s\n",regnames[zreg]); // taken care of by load_reg
                    } else {
                        emit(f,"\t;sext\t%s\n",regnames[zreg]);
                    }
                }
                save_result(p);
                continue;


            // Arithmetic / logic

            case COMPARE:
            case TEST:
                compare(p, c);
                continue;

            case MINUS:
                load_reg(zreg,&p->q1,t);
                emit(f,"\tneg.%s\t%s\n",dt(t),regnames[zreg]);
                save_result(p);
                continue;

            case KOMPLEMENT:
                load_reg(zreg,&p->q1,t);
                emit(f,"\tcpl.%s\t%s\n",dt(t),regnames[zreg]);
                save_result(p);
                continue;            

            case OR:
            case XOR:
            case AND:
            case LSHIFT:
            case RSHIFT:
            case ADD:
            case SUB:
            case MULT:
            case DIV:
            case MOD:
                arithmetic(p, c);
                continue;


            // Load address of object
            case ADDRESS:
                load_address(zreg,&p->q1,POINTER);
                save_result(p);
                continue;

            // Push function argument
            case PUSH:
                if (t==0) ierror(0);
                allocate_result_reg(p, 0);
                load_reg(zreg, &p->q1, t);
                
                emit(f,"\tpush  ");
                emit(f, "%s", regnames[zreg]);
                //emit_obj(f,&p->q1,t, 0);
                emit(f,"\n");

                function_arg_bytes += regsize[zreg];
                stackoffset += regsize[zreg];
                continue;

        }

        if(c==SETRETURN){
          load_reg(p->z.reg,&p->q1,t);
          BSET(regs_modified,p->z.reg);
          continue;
        }

        if(c==GETRETURN){
          if(p->q1.reg){
            zreg=p->q1.reg;
        save_result(p);
          }else
            p->z.flags=0;
          continue;
        }

    // Unhandled IC
    pric2(stdout,p);
    ierror(0);
  }

  function_bottom(f, v, stacksize);
  // if(stack_valid){
  //   if(!v->fi) v->fi=new_fi();
  //   v->fi->flags|=ALL_STACK;
  //   v->fi->stack1=stack;
  // }
  // emit(f,"; stacksize=%lu%s\n",zum2ul(stack),stack_valid?"":"+??");
}




int reg_parm(struct reg_handle *m, struct Typ *t,int vararg,struct Typ *d)
{
  int f;
  f = t->flags & NQ;
  if (f<=LONG||f==POINTER) {
    if (m->gregs>=GPR_ARGS)
      return 0;
    else
      return 1 + 3+m->gregs++;
  }
  if (ISFLOAT(f)) {
    return 0;
    //if(m->fregs>=FPR_ARGS)
//      return 0;
    //else
      //return 0;//FIRST_FPR+2+m->fregs++;
  }
  return 0;
}

int handle_pragma(const char *s) {}



