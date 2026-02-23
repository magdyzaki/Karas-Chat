/**
 * واجهة موحدة للقاعدة: عند ضبط DATABASE_URL تُستخدم Postgres (تدوم البيانات).
 * وإلا تُستخدم lowdb (البيانات تُفقد عند إعادة التشغيل على Render).
 */
import { db as lowDb } from './db.js';
import * as pg from './db-pg.js';

const usePg = !!process.env.DATABASE_URL;

async function runPg(pgFn, lowFn, ...args) {
  if (!usePg) return lowFn.apply(lowDb, args);
  try {
    const result = await pgFn(...args);
    if (result !== null && result !== undefined) return result;
  } catch (e) {
    console.error('db-pg fallback:', e.message);
  }
  return lowFn.apply(lowDb, args);
}

export const db = {
  findUserById: (id) => runPg(pg.pgFindUserById, lowDb.findUserById, id),
  findUserByEmail: (email) => runPg(pg.pgFindUserByEmail, lowDb.findUserByEmail, email),
  findUserByPhone: (phone) => runPg(pg.pgFindUserByPhone, lowDb.findUserByPhone, phone),
  addUser: (data) => runPg(pg.pgAddUser, lowDb.addUser, data),
  isUserBlocked: (id) => runPg(pg.pgIsUserBlocked, lowDb.isUserBlocked, id),
  setUserVerified: (id, v) => runPg(pg.pgSetUserVerified, lowDb.setUserVerified, id, v),
  updateUserProfile: (id, data) => runPg(pg.pgUpdateUserProfile, lowDb.updateUserProfile, id, data),
  setUserLastSeen: (id) => runPg(pg.pgSetUserLastSeen, lowDb.setUserLastSeen, id),
  getConversationPref: (uid, cid) => runPg(pg.pgGetConversationPref, lowDb.getConversationPref, uid, cid),
  getMemberIds: (cid) => runPg(pg.pgGetMemberIds, lowDb.getMemberIds, cid),
  getOrCreateDirectConversation: (u1, u2) => runPg(pg.pgGetOrCreateDirectConversation, lowDb.getOrCreateDirectConversation, u1, u2),
  createGroupConversation: (creator, name, ids) => runPg(pg.pgCreateGroupConversation, lowDb.createGroupConversation, creator, name, ids),
  getConversationByIdAndUser: (cid, uid) => runPg(pg.pgGetConversationByIdAndUser, lowDb.getConversationByIdAndUser, cid, uid),
  getConversationsForUser: (uid) => runPg(pg.pgGetConversationsForUser, lowDb.getConversationsForUser, uid),
  addMessage: (data) => runPg(pg.pgAddMessage, lowDb.addMessage, data),
  getMessagesForConversation: (cid, limit, before, uid) => runPg(pg.pgGetMessagesForConversation, lowDb.getMessagesForConversation, cid, limit, before, uid),
  setConversationRead: (cid, uid, mid) => runPg(pg.pgSetConversationRead, lowDb.setConversationRead, cid, uid, mid),
  getConversationReads: (cid) => runPg(pg.pgGetConversationReads, lowDb.getConversationReads, cid),
  deleteMessageForMe: (mid, cid, uid) => runPg(pg.pgDeleteMessageForMe, lowDb.deleteMessageForMe, mid, cid, uid),
  deleteMessageForEveryone: (mid, cid, uid) => runPg(pg.pgDeleteMessageForEveryone, lowDb.deleteMessageForEveryone, mid, cid, uid),
  addMessageReaction: (mid, uid, emoji) => runPg(pg.pgAddMessageReaction, lowDb.addMessageReaction, mid, uid, emoji),
  removeMessageReaction: (mid, uid) => runPg(pg.pgRemoveMessageReaction, lowDb.removeMessageReaction, mid, uid),
  getMessageReactions: (cid) => runPg(pg.pgGetMessageReactions, lowDb.getMessageReactions, cid),
  getPollVotes: (cid) => runPg(pg.pgGetPollVotes, lowDb.getPollVotes, cid),
  isMessageInConversation: (mid, cid) => runPg(pg.pgIsMessageInConversation, lowDb.isMessageInConversation, mid, cid),
  addPollVote: (mid, cid, uid, opt) => runPg(pg.pgAddPollVote, lowDb.addPollVote, mid, cid, uid, opt),
  listUsersExcept: (uid) => runPg(pg.pgListUsersExcept, lowDb.listUsersExcept, uid),
  getArchivedConversationIds: (uid) => runPg(pg.pgGetArchivedConversationIds, lowDb.getArchivedConversationIds, uid),
  getUnverifiedUsers: () => runPg(pg.pgGetUnverifiedUsers, lowDb.getUnverifiedUsers),

  getUserPublicKey: (id) => (usePg ? pg.pgGetUserPublicKey(id) : Promise.resolve(lowDb.getUserPublicKey(id))),

  findUserByEmailOrPhone: async (input) => {
    const s = (input || '').trim();
    if (!s) return null;
    if (s.includes('@')) return runPg(pg.pgFindUserByEmail, lowDb.findUserByEmail, s);
    return runPg(pg.pgFindUserByPhone, lowDb.findUserByPhone, s);
  },
  setResetCode: (id, code, exp) => lowDb.setResetCode(id, code, exp),
  updateUserPassword: (id, hash) => lowDb.updateUserPassword(id, hash),
  blockUser: (id) => lowDb.blockUser(id),
  unblockUser: (id) => lowDb.unblockUser(id),
  resetAll: () => lowDb.resetAll(),
  getBlockedUsers: () => lowDb.getBlockedUsers(),
  setConversationMuted: (a, b, c) => lowDb.setConversationMuted(a, b, c),
  setConversationArchived: (a, b, c) => lowDb.setConversationArchived(a, b, c),
  isConversationMuted: (a, b) => lowDb.isConversationMuted(a, b),
  setConversationDisappearing: (a, b, c) => lowDb.setConversationDisappearing(a, b, c),
  createInviteLink: (id) => lowDb.createInviteLink(id),
  consumeInviteLink: (tok) => lowDb.consumeInviteLink(tok),
  getInviteLink: (tok) => lowDb.getInviteLink(tok),
  leaveConversation: (a, b) => lowDb.leaveConversation(a, b),
  deleteConversation: (a, b) => lowDb.deleteConversation(a, b),
  addMemberToGroup: (a, b, c) => lowDb.addMemberToGroup(a, b, c),
  removeMemberFromGroup: (a, b, c) => lowDb.removeMemberFromGroup(a, b, c),
  savePushSubscription: (a, b) => lowDb.savePushSubscription(a, b),
  getPushSubscriptionsForUser: (id) => lowDb.getPushSubscriptionsForUser(id),
  removePushSubscription: (a, b) => lowDb.removePushSubscription(a, b),
  getBroadcastLists: (id) => lowDb.getBroadcastLists(id),
  getBroadcastListById: (a, b) => lowDb.getBroadcastListById(a, b),
  createBroadcastList: (a, b, c) => lowDb.createBroadcastList(a, b, c),
  updateBroadcastList: (a, b, c, d) => lowDb.updateBroadcastList(a, b, c, d),
  deleteBroadcastList: (a, b) => lowDb.deleteBroadcastList(a, b),
  setUserPublicKey: (a, b) => lowDb.setUserPublicKey(a, b),
  addStory: (d) => lowDb.addStory(d),
  getStoriesForFeed: (id) => lowDb.getStoriesForFeed(id),
  getStoriesByUser: (id) => lowDb.getStoriesByUser(id),
  findUsersByPhones: (arr, excl) => runPg(pg.pgFindUsersByPhones, lowDb.findUsersByPhones, arr, excl)
};
