import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import api from "@/utils/api";
const router = useRouter();
const loading = ref(false);
const saving = ref(false);
const profile = ref({
    id: null,
    name: "",
    phone: "",
    mobile: "",
    status: "",
    status_text: "",
    balance: 0,
    level: "",
    level_name: "",
    level_discount: 100,
});
const stats = ref({
    total_orders: 0,
    month_reservations: 0,
});
const recentReservations = ref([]);
const recentOrders = ref([]);
// 编辑表单
const editForm = ref({
    name: "",
    phone: "",
});
const formRef = ref();
const rules = {
    name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
    phone: [{ required: true, message: "请输入手机号", trigger: "blur" }],
};
const avatarText = computed(() => {
    if (profile.value.name) {
        return profile.value.name.slice(-2);
    }
    if (profile.value.mobile) {
        return profile.value.mobile.slice(-2);
    }
    return "会员";
});
const currentMonthLabel = computed(() => {
    const d = new Date();
    return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`;
});
function formatDate(val) {
    if (!val)
        return "-";
    if (/^\d{4}-\d{2}-\d{2}$/.test(val))
        return val;
    const d = new Date(val);
    if (Number.isNaN(d.getTime()))
        return val;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}
function formatDateTime(val) {
    if (!val)
        return "-";
    const d = new Date(val);
    if (Number.isNaN(d.getTime()))
        return val;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    return `${y}-${m}-${day} ${hh}:${mm}`;
}
function renderDiscountText(value) {
    if (!value || value >= 100)
        return "原价";
    const raw = value / 10;
    return `${Number.isInteger(raw) ? raw.toFixed(0) : raw.toFixed(1)} 折`;
}
function resetEdit() {
    editForm.value.name = profile.value.name;
    editForm.value.phone = profile.value.mobile || profile.value.phone;
}
/** 保存个人资料 */
async function onSaveProfile() {
    if (!formRef.value)
        return;
    await formRef.value.validate(async (valid) => {
        if (!valid)
            return;
        saving.value = true;
        try {
            await api.put("/member/profile", {
                name: editForm.value.name,
                phone: editForm.value.phone,
            });
            ElMessage.success("资料已保存");
            // 更新本地展示
            profile.value.name = editForm.value.name;
            profile.value.phone = editForm.value.phone;
            profile.value.mobile = editForm.value.phone;
        }
        catch (err) {
            console.error(err);
            const msg = err?.response?.data?.detail || "保存失败";
            ElMessage.error(msg);
        }
        finally {
            saving.value = false;
        }
    });
}
// 路由跳转
const goChangePassword = () => {
    router.push({ path: "/account" });
};
const goReservations = () => {
    router.push({ path: "/reservations" });
};
const goOrders = () => {
    router.push({ path: "/orders" });
};
// 加载数据
async function loadProfile() {
    const res = await api.get("/member/profile");
    const p = res.data || {};
    profile.value = {
        id: p.id ?? null,
        name: p.name || "",
        phone: p.phone || "",
        mobile: p.mobile || p.phone || "",
        status: p.status || "",
        status_text: p.status_text || "已启用",
        balance: Number(p.balance ?? 0),
        level: p.level || "",
        level_name: p.level_name || p.level || "",
        level_discount: Number(p.level_discount ?? 100),
    };
    resetEdit();
}
async function loadOverview() {
    const res = await api.get("/member/overview");
    const ov = res.data || {};
    stats.value = {
        total_orders: Number(ov.total_orders || 0),
        month_reservations: Number(ov.month_reservations || 0),
    };
}
async function loadLists() {
    const [resvRes, ordersRes] = await Promise.all([
        api.get("/member/reservations", { params: { limit: 5 } }),
        api.get("/member/orders", { params: { limit: 5 } }),
    ]);
    recentReservations.value = (resvRes.data || []);
    recentOrders.value = (ordersRes.data || []);
}
async function loadAll() {
    loading.value = true;
    try {
        await Promise.all([loadProfile(), loadOverview(), loadLists()]);
    }
    catch (err) {
        console.error(err);
        const msg = err?.response?.data?.detail || "加载个人中心数据失败";
        ElMessage.error(msg);
    }
    finally {
        loading.value = false;
    }
}
onMounted(() => {
    loadAll();
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['avatar-info']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-info']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-info']} */ ;
/** @type {__VLS_StyleScopedClasses['level-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['security-item']} */ ;
/** @type {__VLS_StyleScopedClasses['security-item']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['list-item']} */ ;
/** @type {__VLS_StyleScopedClasses['item-main']} */ ;
/** @type {__VLS_StyleScopedClasses['item-main']} */ ;
/** @type {__VLS_StyleScopedClasses['item-extra']} */ ;
/** @type {__VLS_StyleScopedClasses['amount']} */ ;
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "center-page" },
});
__VLS_asFunctionalDirective(__VLS_directives.vLoading)(null, { ...__VLS_directiveBindingRestFields, value: (__VLS_ctx.loading) }, null, null);
// @ts-ignore
[vLoading, loading,];
const __VLS_0 = {}.ElRow;
/** @type {[typeof __VLS_components.ElRow, typeof __VLS_components.elRow, typeof __VLS_components.ElRow, typeof __VLS_components.elRow, ]} */ ;
// @ts-ignore
ElRow;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    gutter: (18),
    ...{ class: "top-row" },
}));
const __VLS_2 = __VLS_1({
    gutter: (18),
    ...{ class: "top-row" },
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
const { default: __VLS_4 } = __VLS_3.slots;
const __VLS_5 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_6 = __VLS_asFunctionalComponent(__VLS_5, new __VLS_5({
    span: (16),
}));
const __VLS_7 = __VLS_6({
    span: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_6));
const { default: __VLS_9 } = __VLS_8.slots;
const __VLS_10 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_11 = __VLS_asFunctionalComponent(__VLS_10, new __VLS_10({
    shadow: "hover",
    ...{ class: "profile-card" },
}));
const __VLS_12 = __VLS_11({
    shadow: "hover",
    ...{ class: "profile-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_11));
const { default: __VLS_14 } = __VLS_13.slots;
{
    const { header: __VLS_15 } = __VLS_13.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-sub" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
    if (__VLS_ctx.profile.status_text === '已启用') {
        // @ts-ignore
        [profile,];
        const __VLS_16 = {}.ElTag;
        /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
        // @ts-ignore
        ElTag;
        // @ts-ignore
        const __VLS_17 = __VLS_asFunctionalComponent(__VLS_16, new __VLS_16({
            size: "small",
            type: "success",
        }));
        const __VLS_18 = __VLS_17({
            size: "small",
            type: "success",
        }, ...__VLS_functionalComponentArgsRest(__VLS_17));
        const { default: __VLS_20 } = __VLS_19.slots;
        (__VLS_ctx.profile.status_text);
        // @ts-ignore
        [profile,];
        var __VLS_19;
    }
    else {
        const __VLS_21 = {}.ElTag;
        /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
        // @ts-ignore
        ElTag;
        // @ts-ignore
        const __VLS_22 = __VLS_asFunctionalComponent(__VLS_21, new __VLS_21({
            size: "small",
            type: "danger",
        }));
        const __VLS_23 = __VLS_22({
            size: "small",
            type: "danger",
        }, ...__VLS_functionalComponentArgsRest(__VLS_22));
        const { default: __VLS_25 } = __VLS_24.slots;
        (__VLS_ctx.profile.status_text || '未知状态');
        // @ts-ignore
        [profile,];
        var __VLS_24;
    }
}
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "profile-body" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "avatar-block" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "avatar-circle" },
});
(__VLS_ctx.avatarText);
// @ts-ignore
[avatarText,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "avatar-info" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "name" },
});
(__VLS_ctx.profile.name || "未设置姓名");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "mobile" },
});
(__VLS_ctx.profile.mobile || "-");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "balance" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "amount" },
});
(__VLS_ctx.profile.balance.toFixed(2));
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "level-chip" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.strong, __VLS_intrinsics.strong)({});
(__VLS_ctx.profile.level_name || "普通会员");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "discount" },
});
(__VLS_ctx.renderDiscountText(__VLS_ctx.profile.level_discount));
// @ts-ignore
[profile, renderDiscountText,];
const __VLS_26 = {}.ElDivider;
/** @type {[typeof __VLS_components.ElDivider, typeof __VLS_components.elDivider, ]} */ ;
// @ts-ignore
ElDivider;
// @ts-ignore
const __VLS_27 = __VLS_asFunctionalComponent(__VLS_26, new __VLS_26({}));
const __VLS_28 = __VLS_27({}, ...__VLS_functionalComponentArgsRest(__VLS_27));
const __VLS_31 = {}.ElForm;
/** @type {[typeof __VLS_components.ElForm, typeof __VLS_components.elForm, typeof __VLS_components.ElForm, typeof __VLS_components.elForm, ]} */ ;
// @ts-ignore
ElForm;
// @ts-ignore
const __VLS_32 = __VLS_asFunctionalComponent(__VLS_31, new __VLS_31({
    model: (__VLS_ctx.editForm),
    rules: (__VLS_ctx.rules),
    ref: "formRef",
    labelWidth: "80px",
    size: "small",
    ...{ class: "profile-form" },
}));
const __VLS_33 = __VLS_32({
    model: (__VLS_ctx.editForm),
    rules: (__VLS_ctx.rules),
    ref: "formRef",
    labelWidth: "80px",
    size: "small",
    ...{ class: "profile-form" },
}, ...__VLS_functionalComponentArgsRest(__VLS_32));
/** @type {typeof __VLS_ctx.formRef} */ ;
var __VLS_35 = {};
const { default: __VLS_37 } = __VLS_34.slots;
// @ts-ignore
[editForm, rules, formRef,];
const __VLS_38 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_39 = __VLS_asFunctionalComponent(__VLS_38, new __VLS_38({
    label: "姓名",
    prop: "name",
}));
const __VLS_40 = __VLS_39({
    label: "姓名",
    prop: "name",
}, ...__VLS_functionalComponentArgsRest(__VLS_39));
const { default: __VLS_42 } = __VLS_41.slots;
const __VLS_43 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_44 = __VLS_asFunctionalComponent(__VLS_43, new __VLS_43({
    modelValue: (__VLS_ctx.editForm.name),
    placeholder: "请输入姓名",
    maxlength: "20",
}));
const __VLS_45 = __VLS_44({
    modelValue: (__VLS_ctx.editForm.name),
    placeholder: "请输入姓名",
    maxlength: "20",
}, ...__VLS_functionalComponentArgsRest(__VLS_44));
// @ts-ignore
[editForm,];
var __VLS_41;
const __VLS_48 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({
    label: "手机号",
    prop: "phone",
}));
const __VLS_50 = __VLS_49({
    label: "手机号",
    prop: "phone",
}, ...__VLS_functionalComponentArgsRest(__VLS_49));
const { default: __VLS_52 } = __VLS_51.slots;
const __VLS_53 = {}.ElInput;
/** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
// @ts-ignore
ElInput;
// @ts-ignore
const __VLS_54 = __VLS_asFunctionalComponent(__VLS_53, new __VLS_53({
    modelValue: (__VLS_ctx.editForm.phone),
    placeholder: "请输入手机号",
    maxlength: "20",
}));
const __VLS_55 = __VLS_54({
    modelValue: (__VLS_ctx.editForm.phone),
    placeholder: "请输入手机号",
    maxlength: "20",
}, ...__VLS_functionalComponentArgsRest(__VLS_54));
// @ts-ignore
[editForm,];
var __VLS_51;
const __VLS_58 = {}.ElFormItem;
/** @type {[typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, typeof __VLS_components.ElFormItem, typeof __VLS_components.elFormItem, ]} */ ;
// @ts-ignore
ElFormItem;
// @ts-ignore
const __VLS_59 = __VLS_asFunctionalComponent(__VLS_58, new __VLS_58({}));
const __VLS_60 = __VLS_59({}, ...__VLS_functionalComponentArgsRest(__VLS_59));
const { default: __VLS_62 } = __VLS_61.slots;
const __VLS_63 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_64 = __VLS_asFunctionalComponent(__VLS_63, new __VLS_63({
    ...{ 'onClick': {} },
    type: "primary",
    loading: (__VLS_ctx.saving),
}));
const __VLS_65 = __VLS_64({
    ...{ 'onClick': {} },
    type: "primary",
    loading: (__VLS_ctx.saving),
}, ...__VLS_functionalComponentArgsRest(__VLS_64));
let __VLS_67;
let __VLS_68;
const __VLS_69 = ({ click: {} },
    { onClick: (__VLS_ctx.onSaveProfile) });
const { default: __VLS_70 } = __VLS_66.slots;
// @ts-ignore
[saving, onSaveProfile,];
var __VLS_66;
const __VLS_71 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_72 = __VLS_asFunctionalComponent(__VLS_71, new __VLS_71({
    ...{ 'onClick': {} },
}));
const __VLS_73 = __VLS_72({
    ...{ 'onClick': {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_72));
let __VLS_75;
let __VLS_76;
const __VLS_77 = ({ click: {} },
    { onClick: (__VLS_ctx.resetEdit) });
const { default: __VLS_78 } = __VLS_74.slots;
// @ts-ignore
[resetEdit,];
var __VLS_74;
var __VLS_61;
var __VLS_34;
var __VLS_13;
var __VLS_8;
const __VLS_79 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_80 = __VLS_asFunctionalComponent(__VLS_79, new __VLS_79({
    span: (12),
}));
const __VLS_81 = __VLS_80({
    span: (12),
}, ...__VLS_functionalComponentArgsRest(__VLS_80));
const { default: __VLS_83 } = __VLS_82.slots;
const __VLS_84 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_85 = __VLS_asFunctionalComponent(__VLS_84, new __VLS_84({
    shadow: "hover",
    ...{ class: "security-card" },
}));
const __VLS_86 = __VLS_85({
    shadow: "hover",
    ...{ class: "security-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_85));
const { default: __VLS_88 } = __VLS_87.slots;
{
    const { header: __VLS_89 } = __VLS_87.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-title" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "security-body" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "security-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
(__VLS_ctx.profile.mobile || "-");
// @ts-ignore
[profile,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "security-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
if (__VLS_ctx.profile.status_text === '已启用') {
    // @ts-ignore
    [profile,];
    const __VLS_90 = {}.ElTag;
    /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
    // @ts-ignore
    ElTag;
    // @ts-ignore
    const __VLS_91 = __VLS_asFunctionalComponent(__VLS_90, new __VLS_90({
        size: "small",
        type: "success",
    }));
    const __VLS_92 = __VLS_91({
        size: "small",
        type: "success",
    }, ...__VLS_functionalComponentArgsRest(__VLS_91));
    const { default: __VLS_94 } = __VLS_93.slots;
    var __VLS_93;
}
else {
    const __VLS_95 = {}.ElTag;
    /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
    // @ts-ignore
    ElTag;
    // @ts-ignore
    const __VLS_96 = __VLS_asFunctionalComponent(__VLS_95, new __VLS_95({
        size: "small",
        type: "danger",
    }));
    const __VLS_97 = __VLS_96({
        size: "small",
        type: "danger",
    }, ...__VLS_functionalComponentArgsRest(__VLS_96));
    const { default: __VLS_99 } = __VLS_98.slots;
    (__VLS_ctx.profile.status_text || "未知");
    // @ts-ignore
    [profile,];
    var __VLS_98;
}
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "security-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
const __VLS_100 = {}.ElButton;
/** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
// @ts-ignore
ElButton;
// @ts-ignore
const __VLS_101 = __VLS_asFunctionalComponent(__VLS_100, new __VLS_100({
    ...{ 'onClick': {} },
    type: "primary",
    text: true,
    size: "small",
    ...{ class: "link-btn" },
}));
const __VLS_102 = __VLS_101({
    ...{ 'onClick': {} },
    type: "primary",
    text: true,
    size: "small",
    ...{ class: "link-btn" },
}, ...__VLS_functionalComponentArgsRest(__VLS_101));
let __VLS_104;
let __VLS_105;
const __VLS_106 = ({ click: {} },
    { onClick: (__VLS_ctx.goChangePassword) });
const { default: __VLS_107 } = __VLS_103.slots;
// @ts-ignore
[goChangePassword,];
var __VLS_103;
var __VLS_87;
const __VLS_108 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_109 = __VLS_asFunctionalComponent(__VLS_108, new __VLS_108({
    shadow: "hover",
    ...{ class: "stats-card" },
}));
const __VLS_110 = __VLS_109({
    shadow: "hover",
    ...{ class: "stats-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_109));
const { default: __VLS_112 } = __VLS_111.slots;
{
    const { header: __VLS_113 } = __VLS_111.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "card-title" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stats-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
(__VLS_ctx.stats.total_orders);
// @ts-ignore
[stats,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "desc" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "stat-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "label" },
});
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "value" },
});
(__VLS_ctx.stats.month_reservations);
// @ts-ignore
[stats,];
__VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "desc" },
});
(__VLS_ctx.currentMonthLabel);
// @ts-ignore
[currentMonthLabel,];
var __VLS_111;
var __VLS_82;
var __VLS_3;
const __VLS_114 = {}.ElRow;
/** @type {[typeof __VLS_components.ElRow, typeof __VLS_components.elRow, typeof __VLS_components.ElRow, typeof __VLS_components.elRow, ]} */ ;
// @ts-ignore
ElRow;
// @ts-ignore
const __VLS_115 = __VLS_asFunctionalComponent(__VLS_114, new __VLS_114({
    gutter: (18),
    ...{ class: "bottom-row" },
}));
const __VLS_116 = __VLS_115({
    gutter: (18),
    ...{ class: "bottom-row" },
}, ...__VLS_functionalComponentArgsRest(__VLS_115));
const { default: __VLS_118 } = __VLS_117.slots;
const __VLS_119 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_120 = __VLS_asFunctionalComponent(__VLS_119, new __VLS_119({
    span: (12),
}));
const __VLS_121 = __VLS_120({
    span: (12),
}, ...__VLS_functionalComponentArgsRest(__VLS_120));
const { default: __VLS_123 } = __VLS_122.slots;
const __VLS_124 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_125 = __VLS_asFunctionalComponent(__VLS_124, new __VLS_124({
    shadow: "hover",
    ...{ class: "list-card" },
}));
const __VLS_126 = __VLS_125({
    shadow: "hover",
    ...{ class: "list-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_125));
const { default: __VLS_128 } = __VLS_127.slots;
{
    const { header: __VLS_129 } = __VLS_127.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "list-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    const __VLS_130 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    ElButton;
    // @ts-ignore
    const __VLS_131 = __VLS_asFunctionalComponent(__VLS_130, new __VLS_130({
        ...{ 'onClick': {} },
        type: "primary",
        text: true,
        size: "small",
    }));
    const __VLS_132 = __VLS_131({
        ...{ 'onClick': {} },
        type: "primary",
        text: true,
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_131));
    let __VLS_134;
    let __VLS_135;
    const __VLS_136 = ({ click: {} },
        { onClick: (__VLS_ctx.goReservations) });
    const { default: __VLS_137 } = __VLS_133.slots;
    // @ts-ignore
    [goReservations,];
    var __VLS_133;
}
if (!__VLS_ctx.recentReservations.length) {
    // @ts-ignore
    [recentReservations,];
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "empty-wrapper" },
    });
    const __VLS_138 = {}.ElEmpty;
    /** @type {[typeof __VLS_components.ElEmpty, typeof __VLS_components.elEmpty, ]} */ ;
    // @ts-ignore
    ElEmpty;
    // @ts-ignore
    const __VLS_139 = __VLS_asFunctionalComponent(__VLS_138, new __VLS_138({
        description: "暂无预约记录",
    }));
    const __VLS_140 = __VLS_139({
        description: "暂无预约记录",
    }, ...__VLS_functionalComponentArgsRest(__VLS_139));
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsics.ul, __VLS_intrinsics.ul)({
        ...{ class: "list-body" },
    });
    for (const [item] of __VLS_getVForSourceType((__VLS_ctx.recentReservations))) {
        // @ts-ignore
        [recentReservations,];
        __VLS_asFunctionalElement(__VLS_intrinsics.li, __VLS_intrinsics.li)({
            key: (item.id),
            ...{ class: "list-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-main" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "title" },
        });
        (item.court_name || "未知场地");
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "meta" },
        });
        (__VLS_ctx.formatDate(item.date));
        (item.start_time);
        (item.end_time);
        // @ts-ignore
        [formatDate,];
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-extra" },
        });
        const __VLS_143 = {}.ElTag;
        /** @type {[typeof __VLS_components.ElTag, typeof __VLS_components.elTag, typeof __VLS_components.ElTag, typeof __VLS_components.elTag, ]} */ ;
        // @ts-ignore
        ElTag;
        // @ts-ignore
        const __VLS_144 = __VLS_asFunctionalComponent(__VLS_143, new __VLS_143({
            size: "small",
        }));
        const __VLS_145 = __VLS_144({
            size: "small",
        }, ...__VLS_functionalComponentArgsRest(__VLS_144));
        const { default: __VLS_147 } = __VLS_146.slots;
        (item.status || "-");
        var __VLS_146;
    }
}
var __VLS_127;
var __VLS_122;
const __VLS_148 = {}.ElCol;
/** @type {[typeof __VLS_components.ElCol, typeof __VLS_components.elCol, typeof __VLS_components.ElCol, typeof __VLS_components.elCol, ]} */ ;
// @ts-ignore
ElCol;
// @ts-ignore
const __VLS_149 = __VLS_asFunctionalComponent(__VLS_148, new __VLS_148({
    span: (8),
}));
const __VLS_150 = __VLS_149({
    span: (8),
}, ...__VLS_functionalComponentArgsRest(__VLS_149));
const { default: __VLS_152 } = __VLS_151.slots;
const __VLS_153 = {}.ElCard;
/** @type {[typeof __VLS_components.ElCard, typeof __VLS_components.elCard, typeof __VLS_components.ElCard, typeof __VLS_components.elCard, ]} */ ;
// @ts-ignore
ElCard;
// @ts-ignore
const __VLS_154 = __VLS_asFunctionalComponent(__VLS_153, new __VLS_153({
    shadow: "hover",
    ...{ class: "list-card" },
}));
const __VLS_155 = __VLS_154({
    shadow: "hover",
    ...{ class: "list-card" },
}, ...__VLS_functionalComponentArgsRest(__VLS_154));
const { default: __VLS_157 } = __VLS_156.slots;
{
    const { header: __VLS_158 } = __VLS_156.slots;
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "list-header" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsics.span, __VLS_intrinsics.span)({});
    const __VLS_159 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    ElButton;
    // @ts-ignore
    const __VLS_160 = __VLS_asFunctionalComponent(__VLS_159, new __VLS_159({
        ...{ 'onClick': {} },
        type: "primary",
        text: true,
        size: "small",
    }));
    const __VLS_161 = __VLS_160({
        ...{ 'onClick': {} },
        type: "primary",
        text: true,
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_160));
    let __VLS_163;
    let __VLS_164;
    const __VLS_165 = ({ click: {} },
        { onClick: (__VLS_ctx.goOrders) });
    const { default: __VLS_166 } = __VLS_162.slots;
    // @ts-ignore
    [goOrders,];
    var __VLS_162;
}
if (!__VLS_ctx.recentOrders.length) {
    // @ts-ignore
    [recentOrders,];
    __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "empty-wrapper" },
    });
    const __VLS_167 = {}.ElEmpty;
    /** @type {[typeof __VLS_components.ElEmpty, typeof __VLS_components.elEmpty, ]} */ ;
    // @ts-ignore
    ElEmpty;
    // @ts-ignore
    const __VLS_168 = __VLS_asFunctionalComponent(__VLS_167, new __VLS_167({
        description: "暂无订单记录",
    }));
    const __VLS_169 = __VLS_168({
        description: "暂无订单记录",
    }, ...__VLS_functionalComponentArgsRest(__VLS_168));
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsics.ul, __VLS_intrinsics.ul)({
        ...{ class: "list-body" },
    });
    for (const [item] of __VLS_getVForSourceType((__VLS_ctx.recentOrders))) {
        // @ts-ignore
        [recentOrders,];
        __VLS_asFunctionalElement(__VLS_intrinsics.li, __VLS_intrinsics.li)({
            key: (item.id),
            ...{ class: "list-item" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-main" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "title" },
        });
        (item.type || item.order_no || "订单");
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "meta" },
        });
        (__VLS_ctx.formatDateTime(item.created_at));
        // @ts-ignore
        [formatDateTime,];
        __VLS_asFunctionalElement(__VLS_intrinsics.div, __VLS_intrinsics.div)({
            ...{ class: "item-extra amount" },
        });
        (Number(item.amount || 0).toFixed(2));
    }
}
var __VLS_156;
var __VLS_151;
var __VLS_117;
/** @type {__VLS_StyleScopedClasses['center-page']} */ ;
/** @type {__VLS_StyleScopedClasses['top-row']} */ ;
/** @type {__VLS_StyleScopedClasses['profile-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['card-sub']} */ ;
/** @type {__VLS_StyleScopedClasses['profile-body']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-block']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-circle']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar-info']} */ ;
/** @type {__VLS_StyleScopedClasses['name']} */ ;
/** @type {__VLS_StyleScopedClasses['mobile']} */ ;
/** @type {__VLS_StyleScopedClasses['balance']} */ ;
/** @type {__VLS_StyleScopedClasses['amount']} */ ;
/** @type {__VLS_StyleScopedClasses['level-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['discount']} */ ;
/** @type {__VLS_StyleScopedClasses['profile-form']} */ ;
/** @type {__VLS_StyleScopedClasses['security-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['security-body']} */ ;
/** @type {__VLS_StyleScopedClasses['security-item']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['security-item']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['security-item']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['link-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['stats-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-header']} */ ;
/** @type {__VLS_StyleScopedClasses['card-title']} */ ;
/** @type {__VLS_StyleScopedClasses['stats-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['desc']} */ ;
/** @type {__VLS_StyleScopedClasses['stat-item']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['value']} */ ;
/** @type {__VLS_StyleScopedClasses['desc']} */ ;
/** @type {__VLS_StyleScopedClasses['bottom-row']} */ ;
/** @type {__VLS_StyleScopedClasses['list-card']} */ ;
/** @type {__VLS_StyleScopedClasses['list-header']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['list-body']} */ ;
/** @type {__VLS_StyleScopedClasses['list-item']} */ ;
/** @type {__VLS_StyleScopedClasses['item-main']} */ ;
/** @type {__VLS_StyleScopedClasses['title']} */ ;
/** @type {__VLS_StyleScopedClasses['meta']} */ ;
/** @type {__VLS_StyleScopedClasses['item-extra']} */ ;
/** @type {__VLS_StyleScopedClasses['list-card']} */ ;
/** @type {__VLS_StyleScopedClasses['list-header']} */ ;
/** @type {__VLS_StyleScopedClasses['empty-wrapper']} */ ;
/** @type {__VLS_StyleScopedClasses['list-body']} */ ;
/** @type {__VLS_StyleScopedClasses['list-item']} */ ;
/** @type {__VLS_StyleScopedClasses['item-main']} */ ;
/** @type {__VLS_StyleScopedClasses['title']} */ ;
/** @type {__VLS_StyleScopedClasses['meta']} */ ;
/** @type {__VLS_StyleScopedClasses['item-extra']} */ ;
/** @type {__VLS_StyleScopedClasses['amount']} */ ;
// @ts-ignore
var __VLS_36 = __VLS_35;
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
